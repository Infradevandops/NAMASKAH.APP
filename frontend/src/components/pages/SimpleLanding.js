import React from 'react';

const SimpleLanding = () => {
  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 100%)',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '64px 16px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <h1 style={{
            fontSize: '48px',
            fontWeight: 'bold',
            color: '#1f2937',
            marginBottom: '16px'
          }}>
            Welcome to Namaskah.App
          </h1>
          <p style={{
            fontSize: '24px',
            color: '#6b7280',
            marginBottom: '32px'
          }}>
            Enterprise Communication Platform
          </p>
          <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
            <a 
              href="/api/docs"
              style={{
                backgroundColor: '#2563eb',
                color: 'white',
                padding: '12px 24px',
                borderRadius: '8px',
                textDecoration: 'none',
                display: 'inline-block'
              }}
            >
              API Documentation
            </a>
            <a 
              href="/health"
              style={{
                backgroundColor: '#059669',
                color: 'white',
                padding: '12px 24px',
                borderRadius: '8px',
                textDecoration: 'none',
                display: 'inline-block'
              }}
            >
              Health Check
            </a>
          </div>
        </div>
        
        <div style={{
          marginTop: '64px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '32px'
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}>
            <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '8px' }}>
              SMS Verification
            </h3>
            <p style={{ color: '#6b7280' }}>
              Verify accounts across 100+ services with mock mode enabled
            </p>
          </div>
          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}>
            <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '8px' }}>
              Real-time Chat
            </h3>
            <p style={{ color: '#6b7280' }}>
              Instant messaging with WebSocket support
            </p>
          </div>
          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}>
            <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '8px' }}>
              AI Assistant
            </h3>
            <p style={{ color: '#6b7280' }}>
              Smart automation (disabled in mock mode)
            </p>
          </div>
        </div>
        
        <div style={{
          marginTop: '64px',
          textAlign: 'center',
          padding: '32px',
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
        }}>
          <h2 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '16px' }}>
            Platform Status: Online
          </h2>
          <p style={{ color: '#6b7280', marginBottom: '24px' }}>
            Backend API is running with mock services enabled for development
          </p>
          <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <span style={{
              backgroundColor: '#10b981',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '20px',
              fontSize: '14px'
            }}>
              ✓ Database Connected
            </span>
            <span style={{
              backgroundColor: '#f59e0b',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '20px',
              fontSize: '14px'
            }}>
              ⚠ Mock Services
            </span>
            <span style={{
              backgroundColor: '#10b981',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '20px',
              fontSize: '14px'
            }}>
              ✓ API Ready
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleLanding;