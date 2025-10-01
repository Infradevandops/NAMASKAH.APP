/**
 * WebSocket Connection Manager with Pooling and Optimization
 * Handles multiple WebSocket connections efficiently with connection reuse,
 * automatic reconnection, and performance monitoring.
 */

class WebSocketManager {
  constructor() {
    this.connections = new Map(); // url -> connection
    this.connectionPools = new Map(); // url -> pool of connections
    this.maxConnectionsPerUrl = 5;
    this.reconnectAttempts = 3;
    this.reconnectDelay = 1000; // Start with 1 second
    this.maxReconnectDelay = 30000; // Max 30 seconds
    this.connectionTimeout = 10000; // 10 seconds
    this.heartbeatInterval = 30000; // 30 seconds
    this.messageQueue = new Map(); // url -> queue of messages
    this.performanceMetrics = new Map(); // url -> metrics
  }

  /**
   * Get or create a WebSocket connection for a URL
   * @param {string} url - WebSocket URL
   * @param {Object} options - Connection options
   * @returns {Promise<WebSocket>} WebSocket connection
   */
  async getConnection(url, options = {}) {
    const {
      priority = 'normal',
      timeout = this.connectionTimeout,
      enableHeartbeat = true
    } = options;

    // Check if we already have an active connection
    if (this.connections.has(url)) {
      const connection = this.connections.get(url);
      if (this.isConnectionHealthy(connection)) {
        this.updateMetrics(url, 'connection_reused');
        return connection;
      } else {
        // Clean up unhealthy connection
        this.closeConnection(url);
      }
    }

    // Try to get from pool
    const pool = this.connectionPools.get(url) || [];
    const availableConnection = pool.find(conn => this.isConnectionHealthy(conn));

    if (availableConnection) {
      this.connections.set(url, availableConnection);
      this.updateMetrics(url, 'connection_from_pool');
      return availableConnection;
    }

    // Create new connection
    return this.createConnection(url, { priority, timeout, enableHeartbeat });
  }

  /**
   * Create a new WebSocket connection
   * @param {string} url - WebSocket URL
   * @param {Object} options - Connection options
   * @returns {Promise<WebSocket>} WebSocket connection
   */
  async createConnection(url, options = {}) {
    const { priority, timeout, enableHeartbeat } = options;

    return new Promise((resolve, reject) => {
      const startTime = Date.now();

      try {
        const ws = new WebSocket(url);

        // Set up event handlers
        ws.onopen = () => {
          const connectionTime = Date.now() - startTime;
          this.connections.set(url, ws);
          this.updateMetrics(url, 'connection_established', { connectionTime });

          if (enableHeartbeat) {
            this.startHeartbeat(url, ws);
          }

          // Send queued messages
          this.sendQueuedMessages(url, ws);

          resolve(ws);
        };

        ws.onmessage = (event) => {
          this.updateMetrics(url, 'message_received');
          // Handle incoming messages if needed
        };

        ws.onerror = (error) => {
          this.updateMetrics(url, 'connection_error');
          console.error(`WebSocket error for ${url}:`, error);
          reject(error);
        };

        ws.onclose = (event) => {
          this.updateMetrics(url, 'connection_closed', { code: event.code });
          this.handleConnectionClose(url, ws, event);
        };

        // Set connection timeout
        setTimeout(() => {
          if (ws.readyState === WebSocket.CONNECTING) {
            ws.close();
            reject(new Error(`Connection timeout for ${url}`));
          }
        }, timeout);

      } catch (error) {
        this.updateMetrics(url, 'connection_failed');
        reject(error);
      }
    });
  }

  /**
   * Send a message through the WebSocket connection
   * @param {string} url - WebSocket URL
   * @param {string|Object} message - Message to send
   * @param {Object} options - Send options
   */
  async sendMessage(url, message, options = {}) {
    const { priority = 'normal', retry = true } = options;

    const connection = await this.getConnection(url, { priority });

    if (connection.readyState === WebSocket.OPEN) {
      const messageData = typeof message === 'string' ? message : JSON.stringify(message);
      connection.send(messageData);
      this.updateMetrics(url, 'message_sent');
    } else {
      // Queue message for later
      this.queueMessage(url, message);
      if (retry) {
        // Retry after a short delay
        setTimeout(() => this.sendMessage(url, message, { ...options, retry: false }), 1000);
      }
    }
  }

  /**
   * Queue a message for sending when connection is available
   * @param {string} url - WebSocket URL
   * @param {string|Object} message - Message to queue
   */
  queueMessage(url, message) {
    if (!this.messageQueue.has(url)) {
      this.messageQueue.set(url, []);
    }
    this.messageQueue.get(url).push(message);
  }

  /**
   * Send all queued messages for a URL
   * @param {string} url - WebSocket URL
   * @param {WebSocket} connection - WebSocket connection
   */
  sendQueuedMessages(url, connection) {
    const queue = this.messageQueue.get(url) || [];
    if (queue.length > 0 && connection.readyState === WebSocket.OPEN) {
      queue.forEach(message => {
        const messageData = typeof message === 'string' ? message : JSON.stringify(message);
        connection.send(messageData);
        this.updateMetrics(url, 'queued_message_sent');
      });
      this.messageQueue.delete(url);
    }
  }

  /**
   * Start heartbeat for a connection
   * @param {string} url - WebSocket URL
   * @param {WebSocket} ws - WebSocket connection
   */
  startHeartbeat(url, ws) {
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
        this.updateMetrics(url, 'heartbeat_sent');
      } else {
        clearInterval(heartbeat);
      }
    }, this.heartbeatInterval);

    // Store heartbeat reference for cleanup
    ws.heartbeat = heartbeat;
  }

  /**
   * Handle connection close with reconnection logic
   * @param {string} url - WebSocket URL
   * @param {WebSocket} ws - WebSocket connection
   * @param {Event} event - Close event
   */
  handleConnectionClose(url, ws, event) {
    this.connections.delete(url);

    // Clean up heartbeat
    if (ws.heartbeat) {
      clearInterval(ws.heartbeat);
    }

    // Add to pool if connection was clean
    if (event.code === 1000 || event.code === 1001) {
      this.addToPool(url, ws);
    }

    // Attempt reconnection for unexpected closes
    if (event.code !== 1000 && event.code !== 1001) {
      this.attemptReconnection(url);
    }
  }

  /**
   * Attempt to reconnect to a WebSocket URL
   * @param {string} url - WebSocket URL
   * @param {number} attempt - Current attempt number
   */
  async attemptReconnection(url, attempt = 1) {
    if (attempt > this.reconnectAttempts) {
      this.updateMetrics(url, 'reconnection_failed');
      return;
    }

    const delay = Math.min(this.reconnectDelay * Math.pow(2, attempt - 1), this.maxReconnectDelay);

    setTimeout(async () => {
      try {
        await this.createConnection(url);
        this.updateMetrics(url, 'reconnection_successful');
      } catch (error) {
        this.attemptReconnection(url, attempt + 1);
      }
    }, delay);
  }

  /**
   * Add connection to pool for reuse
   * @param {string} url - WebSocket URL
   * @param {WebSocket} ws - WebSocket connection
   */
  addToPool(url, ws) {
    if (!this.connectionPools.has(url)) {
      this.connectionPools.set(url, []);
    }

    const pool = this.connectionPools.get(url);
    if (pool.length < this.maxConnectionsPerUrl) {
      pool.push(ws);
      this.updateMetrics(url, 'connection_pooled');
    } else {
      ws.close();
    }
  }

  /**
   * Check if a WebSocket connection is healthy
   * @param {WebSocket} ws - WebSocket connection
   * @returns {boolean} Whether connection is healthy
   */
  isConnectionHealthy(ws) {
    return ws && ws.readyState === WebSocket.OPEN;
  }

  /**
   * Close a specific connection
   * @param {string} url - WebSocket URL
   */
  closeConnection(url) {
    const connection = this.connections.get(url);
    if (connection) {
      connection.close();
      this.connections.delete(url);
    }
  }

  /**
   * Close all connections and clean up
   */
  closeAll() {
    // Close active connections
    this.connections.forEach((ws, url) => {
      ws.close();
    });
    this.connections.clear();

    // Close pooled connections
    this.connectionPools.forEach((pool, url) => {
      pool.forEach(ws => ws.close());
    });
    this.connectionPools.clear();

    // Clear message queues
    this.messageQueue.clear();
  }

  /**
   * Update performance metrics
   * @param {string} url - WebSocket URL
   * @param {string} event - Event type
   * @param {Object} data - Additional data
   */
  updateMetrics(url, event, data = {}) {
    if (!this.performanceMetrics.has(url)) {
      this.performanceMetrics.set(url, {
        connectionsEstablished: 0,
        connectionsReused: 0,
        connectionsFromPool: 0,
        connectionsPooled: 0,
        messagesSent: 0,
        messagesReceived: 0,
        queuedMessagesSent: 0,
        heartbeatsSent: 0,
        errors: 0,
        reconnectionsSuccessful: 0,
        reconnectionsFailed: 0,
        totalConnectionTime: 0,
        averageConnectionTime: 0
      });
    }

    const metrics = this.performanceMetrics.get(url);

    switch (event) {
      case 'connection_established':
        metrics.connectionsEstablished++;
        if (data.connectionTime) {
          metrics.totalConnectionTime += data.connectionTime;
          metrics.averageConnectionTime = metrics.totalConnectionTime / metrics.connectionsEstablished;
        }
        break;
      case 'connection_reused':
        metrics.connectionsReused++;
        break;
      case 'connection_from_pool':
        metrics.connectionsFromPool++;
        break;
      case 'connection_pooled':
        metrics.connectionsPooled++;
        break;
      case 'message_sent':
        metrics.messagesSent++;
        break;
      case 'message_received':
        metrics.messagesReceived++;
        break;
      case 'queued_message_sent':
        metrics.queuedMessagesSent++;
        break;
      case 'heartbeat_sent':
        metrics.heartbeatsSent++;
        break;
      case 'connection_error':
      case 'connection_failed':
        metrics.errors++;
        break;
      case 'reconnection_successful':
        metrics.reconnectionsSuccessful++;
        break;
      case 'reconnection_failed':
        metrics.reconnectionsFailed++;
        break;
    }
  }

  /**
   * Get performance metrics for a URL
   * @param {string} url - WebSocket URL
   * @returns {Object} Performance metrics
   */
  getMetrics(url) {
    return this.performanceMetrics.get(url) || {};
  }

  /**
   * Get all performance metrics
   * @returns {Object} All performance metrics
   */
  getAllMetrics() {
    const allMetrics = {};
    this.performanceMetrics.forEach((metrics, url) => {
      allMetrics[url] = metrics;
    });
    return allMetrics;
  }
}

// Export singleton instance
export const webSocketManager = new WebSocketManager();
export default WebSocketManager;
