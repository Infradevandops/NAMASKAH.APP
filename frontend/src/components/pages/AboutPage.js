import React from 'react';
import { Link } from 'react-router-dom';
import { Button, Typography, Card } from '../atoms';

const AboutPage = () => {
  const teamMembers = [
    {
      name: "Alex Johnson",
      role: "CEO & Founder",
      bio: "10+ years in telecommunications and enterprise software. Previously led product at major telecom companies.",
      avatar: "AJ",
      linkedin: "#"
    },
    {
      name: "Sarah Chen",
      role: "CTO",
      bio: "Former senior engineer at Google and Twilio. Expert in scalable communication infrastructure.",
      avatar: "SC",
      linkedin: "#"
    },
    {
      name: "Marcus Rodriguez",
      role: "Head of Product",
      bio: "Product leader with experience at Stripe and Slack. Focused on developer experience and API design.",
      avatar: "MR",
      linkedin: "#"
    },
    {
      name: "Jennifer Park",
      role: "VP of Engineering",
      bio: "Engineering leader with 8+ years building high-scale systems. Previously at Uber and Airbnb.",
      avatar: "JP",
      linkedin: "#"
    }
  ];

  const values = [
    {
      icon: "🚀",
      title: "Innovation",
      description: "We constantly push the boundaries of what's possible in communication technology."
    },
    {
      icon: "🔒",
      title: "Security",
      description: "Enterprise-grade security and compliance are built into everything we do."
    },
    {
      icon: "🌍",
      title: "Global Scale",
      description: "Our platform is designed to work reliably across the globe, 24/7."
    },
    {
      icon: "🤝",
      title: "Partnership",
      description: "We believe in building long-term partnerships with our customers and community."
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
      <nav className="bg-white shadow-sm fixed w-full top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link to="/" className="text-2xl font-bold text-blue-600">
                namaskah
              </Link>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <Link to="/" className="text-gray-600 hover:text-blue-600">Home</Link>
              <Link to="/about" className="text-blue-600 font-semibold">About</Link>
              <Link to="/reviews" className="text-gray-600 hover:text-blue-600">Reviews</Link>
              <Link to="/login" className="text-gray-600 hover:text-blue-600">Login</Link>
              <Link to="/register">
                <Button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
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
          <div className="max-w-4xl mx-auto text-center">
            <Typography variant="h1" className="text-5xl font-bold mb-6 leading-tight text-white">
              About namaskah
            </Typography>
            <Typography variant="body" className="text-xl mb-8 text-blue-100">
              We're building the future of communication infrastructure. 
              Our mission is to make reliable, scalable communication accessible to every developer and business.
            </Typography>
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

      {/* Mission Section */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <Typography variant="h2" className="text-3xl font-bold mb-4">
                Our Mission
              </Typography>
              <Typography className="text-xl text-gray-600">
                Empowering developers and businesses with reliable communication infrastructure
              </Typography>
            </div>
            
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <Typography className="text-lg text-gray-700 mb-6">
                  Founded in 2024, namaskah was born from the frustration of dealing with unreliable 
                  SMS verification services and fragmented communication APIs. We saw developers 
                  struggling with multiple providers, inconsistent APIs, and poor reliability.
                </Typography>
                <Typography className="text-lg text-gray-700 mb-6">
                  Our platform unifies SMS verification, real-time messaging, and voice communication 
                  into a single, developer-friendly API. We handle the complexity so you can focus 
                  on building great products.
                </Typography>
                <Typography className="text-lg text-gray-700">
                  Today, we're trusted by over 500 companies worldwide, from startups to Fortune 500 
                  enterprises, processing millions of messages with 99.9% uptime.
                </Typography>
              </div>
              <div className="text-center">
                <div className="bg-white rounded-2xl p-8 shadow-lg">
                  <div className="text-6xl mb-4">🚀</div>
                  <Typography variant="h3" className="text-2xl font-bold mb-4">Our Vision</Typography>
                  <Typography className="text-gray-600">
                    To become the global standard for communication infrastructure, 
                    enabling seamless connections between businesses and their customers.
                  </Typography>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <Typography variant="h2" className="text-3xl font-bold mb-4">
              Our Values
            </Typography>
            <Typography className="text-xl text-gray-600">
              The principles that guide everything we do
            </Typography>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {values.map((value, index) => (
              <Card key={index} className="p-6 text-center hover:shadow-lg transition-shadow">
                <div className="text-4xl mb-4">{value.icon}</div>
                <Typography variant="h3" className="text-xl font-semibold mb-3">
                  {value.title}
                </Typography>
                <Typography className="text-gray-600">
                  {value.description}
                </Typography>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <Typography variant="h2" className="text-3xl font-bold mb-4">
              Meet Our Team
            </Typography>
            <Typography className="text-xl text-gray-600">
              Experienced leaders from top tech companies
            </Typography>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {teamMembers.map((member, index) => (
              <Card key={index} className="p-6 text-center hover:shadow-lg transition-shadow">
                <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-xl mx-auto mb-4">
                  {member.avatar}
                </div>
                <Typography variant="h4" className="text-lg font-semibold mb-2">
                  {member.name}
                </Typography>
                <Typography className="text-blue-600 font-medium mb-3">
                  {member.role}
                </Typography>
                <Typography className="text-gray-600 text-sm mb-4">
                  {member.bio}
                </Typography>
                <a 
                  href={member.linkedin} 
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  Connect on LinkedIn →
                </a>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-16 bg-blue-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <Typography variant="h2" className="text-3xl font-bold mb-4 text-white">
            Get in Touch
          </Typography>
          <Typography className="text-xl mb-8 text-blue-100 max-w-2xl mx-auto">
            Have questions about our platform? Want to learn more about enterprise solutions? 
            We'd love to hear from you.
          </Typography>
          
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            <div>
              <div className="text-3xl mb-3">📧</div>
              <Typography className="font-semibold mb-2 text-white">Email Us</Typography>
              <Typography className="text-blue-100">hello@namaskah.com</Typography>
              <Typography className="text-blue-100">support@namaskah.com</Typography>
            </div>
            <div>
              <div className="text-3xl mb-3">💬</div>
              <Typography className="font-semibold mb-2 text-white">Live Chat</Typography>
              <Typography className="text-blue-100">Available 24/7</Typography>
              <Typography className="text-blue-100">Average response: 2 minutes</Typography>
            </div>
            <div>
              <div className="text-3xl mb-3">📞</div>
              <Typography className="font-semibold mb-2 text-white">Phone Support</Typography>
              <Typography className="text-blue-100">Enterprise customers</Typography>
              <Typography className="text-blue-100">Dedicated account managers</Typography>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 w-full sm:w-auto">
                Start Free Trial
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600 w-full sm:w-auto">
                Contact Sales
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <Link to="/" className="text-2xl font-bold text-white">
                namaskah
              </Link>
              <Typography className="text-gray-400 mt-2">
                Enterprise communication platform
              </Typography>
            </div>
            <div className="flex space-x-6">
              <Link to="/" className="text-gray-400 hover:text-white">Home</Link>
              <Link to="/about" className="text-gray-400 hover:text-white">About</Link>
              <Link to="/reviews" className="text-gray-400 hover:text-white">Reviews</Link>
              <a href="/docs" className="text-gray-400 hover:text-white">Docs</a>
            </div>
          </div>
          <div className="border-t border-gray-700 mt-6 pt-6 text-center">
            <Typography className="text-gray-400">
              © 2024 namaskah. All rights reserved.
            </Typography>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AboutPage;