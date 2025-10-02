import React from 'react';
import { Link } from 'react-router-dom';
import { Button, Typography, Card, Badge } from '../atoms';

const LandingPage = () => {
  const testimonials = [
    {
      name: "Sarah Chen",
      role: "CTO at TechFlow Solutions",
      company: "TechFlow Solutions",
      rating: 5,
      text: "CumApp reduced our SMS verification costs by 40% while improving delivery rates. The AI-powered features are incredible - it automatically handles customer queries and escalates complex issues. Setup took less than an hour.",
      avatar: "SC"
    },
    {
      name: "Marcus Rodriguez", 
      role: "Lead Developer at StartupHub",
      company: "StartupHub",
      rating: 5,
      text: "We migrated from Twilio + custom chat solution to CumApp. The unified platform saved us 6 months of development time. Real-time features work flawlessly, and the React components are beautiful.",
      avatar: "MR"
    },
    {
      name: "Jennifer Park",
      role: "Product Manager at GrowthCorp", 
      company: "GrowthCorp",
      rating: 5,
      text: "Implementation was smooth thanks to comprehensive docs. When we had questions, support responded within hours. The platform scales effortlessly - we went from 1K to 100K users without issues.",
      avatar: "JP"
    },
    {
      name: "David Thompson",
      role: "Security Lead at EnterpriseMax",
      company: "EnterpriseMax", 
      rating: 5,
      text: "Security features are top-notch. GDPR compliance, audit trails, and role-based access made our compliance team happy. The multi-tenant architecture works perfectly for our B2B SaaS.",
      avatar: "DT"
    }
  ];

  const features = [
    {
      icon: "📱",
      title: "SMS Verification",
      description: "100+ services including WhatsApp, Telegram, Google, Discord with 99.5% delivery rates"
    },
    {
      icon: "🤖", 
      title: "AI-Powered",
      description: "Intelligent conversation assistance, auto-responses, and sentiment analysis"
    },
    {
      icon: "⚡",
      title: "Real-time Chat",
      description: "WebSocket-based messaging with typing indicators and read receipts"
    },
    {
      icon: "🛡️",
      title: "Enterprise Security", 
      description: "SOC2 ready, GDPR compliant, with advanced security headers and monitoring"
    },
    {
      icon: "🌍",
      title: "Global Scale",
      description: "Multi-region deployment with <100ms response times worldwide"
    },
    {
      icon: "📊",
      title: "Advanced Analytics",
      description: "Real-time metrics, cost tracking, and performance insights dashboard"
    }
  ];

  const stats = [
    { number: "500+", label: "Companies Trust Us" },
    { number: "50K+", label: "Developers" },
    { number: "10M+", label: "Messages Sent" },
    { number: "99.9%", label: "Uptime SLA" }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="bg-black shadow-sm fixed w-full top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link to="/" className="text-2xl font-bold text-white">
                Namaskah.App
              </Link>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <Link to="/about" className="text-gray-300 hover:text-white">About</Link>
              <Link to="/reviews" className="text-gray-300 hover:text-white">Reviews</Link>
              <Link to="/login" className="text-gray-300 hover:text-white">Login</Link>
              <Link to="/register">
                <Button className="bg-white text-black px-4 py-2 rounded-lg hover:bg-gray-200">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-600 text-white pt-20 pb-16">
        <div className="container mx-auto px-4 py-16">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <Typography variant="h1" className="text-5xl font-bold mb-6 leading-tight text-white">
                Enterprise Communication Platform
              </Typography>
              <Typography variant="body" className="text-xl mb-8 text-blue-100">
                SMS verification, AI-powered messaging, and real-time chat in one unified platform. 
                Trusted by 500+ companies worldwide.
              </Typography>
              
              {/* Trust Indicators */}
              <div className="flex items-center mb-6 space-x-4">
                <div className="flex items-center">
                  <span className="text-yellow-400">⭐⭐⭐⭐⭐</span>
                  <span className="ml-2 text-blue-100">4.8/5 on Trustpilot</span>
                </div>
                <div className="text-blue-100">•</div>
                <div className="text-blue-100">247 reviews</div>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 mb-6">
                <Link to="/register">
                  <Button className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold hover:bg-gray-100 w-full sm:w-auto">
                    🚀 Start Free Trial
                  </Button>
                </Link>
                <a href="/docs" target="_blank" rel="noopener noreferrer">
                  <Button variant="outline" className="border-2 border-white text-white px-8 py-4 rounded-lg font-semibold hover:bg-white hover:text-blue-600 w-full sm:w-auto">
                    📖 View Documentation
                  </Button>
                </a>
              </div>
              
              <div className="flex items-center text-blue-100">
                <span className="mr-2">✅</span>
                <span>No credit card required • 1K free SMS monthly • 5-minute setup</span>
              </div>
            </div>
            
            <div className="text-center">
              <div className="bg-white/10 rounded-2xl p-8 backdrop-blur-sm">
                <div className="text-6xl mb-4">📱</div>
                <Typography variant="h3" className="text-white mb-2">Ready in Minutes</Typography>
                <Typography className="text-blue-100">
                  Complete platform setup with our quick-start guide
                </Typography>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {stats.map((stat, index) => (
              <div key={index}>
                <Typography variant="h2" className="text-3xl font-bold text-blue-600 mb-2">
                  {stat.number}
                </Typography>
                <Typography className="text-gray-600">{stat.label}</Typography>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <Typography variant="h2" className="text-3xl font-bold mb-4 text-black">
              Everything You Need in One Platform
            </Typography>
            <Typography className="text-xl max-w-2xl mx-auto text-gray-600">
              From SMS verification to enterprise communication suite - 
              Namaskah.App grows with your business needs.
            </Typography>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="p-6 text-center hover:shadow-lg transition-shadow">
                <div className="text-4xl mb-4">{feature.icon}</div>
                <Typography variant="h3" className="text-xl font-semibold mb-3">
                  {feature.title}
                </Typography>
                <Typography className="text-gray-600">
                  {feature.description}
                </Typography>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center mb-4">
              <img src="/trustpilot-logo.svg" alt="Trustpilot" className="h-8 mr-4" />
              <div className="flex items-center">
                <span className="text-yellow-400 text-2xl">⭐⭐⭐⭐⭐</span>
                <span className="ml-2 text-lg font-semibold">4.8/5</span>
                <span className="ml-2 text-gray-600">(247 reviews)</span>
              </div>
            </div>
            <Typography variant="h2" className="text-3xl font-bold mb-4">
              Trusted by Industry Leaders
            </Typography>
            <Typography className="text-xl text-gray-600">
              See what our customers say about CumApp
            </Typography>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="p-6">
                <div className="flex items-center mb-4">
                  <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold mr-4">
                    {testimonial.avatar}
                  </div>
                  <div>
                    <Typography variant="h4" className="font-semibold">
                      {testimonial.name}
                    </Typography>
                    <Typography className="text-gray-600 text-sm">
                      {testimonial.role}
                    </Typography>
                    <div className="flex items-center mt-1">
                      <span className="text-yellow-400">⭐⭐⭐⭐⭐</span>
                      <Badge variant="outline" className="ml-2 text-xs">
                        Verified
                      </Badge>
                    </div>
                  </div>
                </div>
                <Typography className="text-gray-700 italic">
                  "{testimonial.text}"
                </Typography>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-blue-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <Typography variant="h2" className="text-3xl font-bold mb-4 text-white">
            Ready to Transform Your Communication?
          </Typography>
          <Typography className="text-xl mb-8 text-blue-100 max-w-2xl mx-auto">
            Join 500+ companies using CumApp for reliable, scalable communication infrastructure.
          </Typography>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <Link to="/register">
              <Button className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold hover:bg-gray-100 w-full sm:w-auto">
                🚀 Start Free Trial
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" className="border-2 border-white text-white px-8 py-4 rounded-lg font-semibold hover:bg-white hover:text-blue-600 w-full sm:w-auto">
                📞 Login to Dashboard
              </Button>
            </Link>
          </div>
          
          <div className="flex items-center justify-center text-blue-100">
            <span className="mr-2">✅</span>
            <span>14-day free trial • No setup fees • Cancel anytime</span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;