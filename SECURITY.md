# Security Policy

## Supported Versions

We actively support the following versions of namaskah with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in namaskah, please follow these steps:

### 🚨 **DO NOT** create a public GitHub issue for security vulnerabilities

### Instead, please:

1. **Email us directly** at: `security@infradevandops.com`
2. **Include the following information:**
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Any suggested fixes (if available)
   - Your contact information

### What to expect:

- **Acknowledgment**: We will acknowledge receipt of your report within 24 hours
- **Initial Assessment**: We will provide an initial assessment within 72 hours
- **Regular Updates**: We will keep you informed of our progress
- **Resolution Timeline**: We aim to resolve critical vulnerabilities within 7 days
- **Credit**: We will credit you in our security advisories (unless you prefer to remain anonymous)

## Security Measures

### Current Security Implementations

1. **API Security**
   - Environment variable configuration for sensitive data
   - Input validation and sanitization
   - Rate limiting on API endpoints
   - CORS configuration

2. **Container Security**
   - Non-root user execution in containers
   - Minimal base images (Python slim)
   - Security scanning of dependencies
   - Health checks and monitoring

3. **Network Security**
   - Nginx reverse proxy with security headers
   - SSL/TLS termination support
   - Rate limiting and DDoS protection
   - Secure communication between services

4. **Data Protection**
   - No storage of sensitive API keys in code
   - Encrypted communication with external APIs
   - Secure session management with Redis
   - Database connection security

### Security Best Practices for Users

1. **Environment Variables**
   ```bash
   # Never commit these to version control
   TEXTVERIFIED_API_KEY=your_secret_key
   TWILIO_AUTH_TOKEN=your_secret_token
   GROQ_API_KEY=your_secret_key
   JWT_SECRET_KEY=your_jwt_secret
   ```

2. **Production Deployment**
   - Use strong, unique passwords for database and Redis
   - Enable SSL/TLS certificates
   - Regularly update Docker images
   - Monitor logs for suspicious activity
   - Implement proper firewall rules

3. **API Key Management**
   - Rotate API keys regularly
   - Use different keys for development and production
   - Monitor API usage for anomalies
   - Implement proper access controls

## Vulnerability Categories

We are particularly interested in reports about:

### High Priority
- Remote code execution
- SQL injection
- Authentication bypass
- Privilege escalation
- Data exposure/leakage

### Medium Priority
- Cross-site scripting (XSS)
- Cross-site request forgery (CSRF)
- Information disclosure
- Denial of service (DoS)
- API abuse

### Low Priority
- Rate limiting bypass
- Minor information leakage
- Configuration issues

## Security Updates

### How we handle security updates:

1. **Critical Vulnerabilities** (CVSS 9.0-10.0)
   - Immediate patch development
   - Emergency release within 24-48 hours
   - Public disclosure after fix deployment

2. **High Vulnerabilities** (CVSS 7.0-8.9)
   - Patch development within 72 hours
   - Release within 7 days
   - Security advisory publication

3. **Medium/Low Vulnerabilities** (CVSS < 7.0)
   - Included in next regular release
   - Documentation updates
   - Best practice recommendations

### Notification Channels

Security updates are communicated through:
- GitHub Security Advisories
- Release notes and changelog
- Docker image tags and descriptions
- Email notifications to registered users

## Secure Development Practices

### Code Review Process
- All code changes require review
- Security-focused code reviews for sensitive areas
- Automated security scanning in CI/CD pipeline
- Dependency vulnerability scanning

### Testing
- Security testing in CI/CD pipeline
- Regular penetration testing
- Automated vulnerability scanning
- Manual security reviews

### Dependencies
- Regular dependency updates
- Automated vulnerability scanning
- Security advisory monitoring
- Minimal dependency principle

## Compliance and Standards

### Standards We Follow
- OWASP Top 10 security risks mitigation
- NIST Cybersecurity Framework guidelines
- Industry best practices for API security
- Docker security best practices

### Regular Security Activities
- Monthly dependency updates
- Quarterly security assessments
- Annual penetration testing
- Continuous monitoring and logging

## Contact Information

For security-related inquiries:
- **Email**: security@infradevandops.com
- **PGP Key**: [Available on request]
- **Response Time**: Within 24 hours

For general questions about this security policy:
- **GitHub Issues**: For non-sensitive questions only
- **Email**: info@infradevandops.com

## Acknowledgments

We would like to thank the following security researchers who have helped improve namaskah's security:

- [Your name could be here - report a vulnerability!]

## Legal

This security policy is subject to our [Terms of Service](https://github.com/Infradevandops/namaskah/blob/main/LICENSE) and applicable laws. We reserve the right to modify this policy at any time.

---

**Last Updated**: December 2024
**Version**: 1.0