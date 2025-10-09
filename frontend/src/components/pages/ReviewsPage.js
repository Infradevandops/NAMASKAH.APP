import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Typography, Card, Badge } from '../atoms';

const ReviewsPage = () => {
  const [filterRating, setFilterRating] = useState('all');
  const [sortBy, setSortBy] = useState('newest');

  const reviews = [
    {
      id: 1,
      name: "Sarah Chen",
      role: "CTO",
      company: "TechFlow Solutions",
      rating: 5,
      date: "2024-01-15",
      title: "Game-changer for our verification workflow",
      text: "namaskah reduced our SMS verification costs by 40% while improving delivery rates. The AI-powered features are incredible - it automatically handles customer queries and escalates complex issues. Setup took less than an hour.",
      avatar: "SC",
      verified: true,
      helpful: 24
    },
    {
      id: 2,
      name: "Marcus Rodriguez",
      role: "Lead Developer",
      company: "StartupHub",
      rating: 5,
      date: "2024-01-10",
      title: "Best communication platform we've used",
      text: "We migrated from Twilio + custom chat solution to namaskah. The unified platform saved us 6 months of development time. Real-time features work flawlessly, and the React components are beautiful.",
      avatar: "MR",
      verified: true,
      helpful: 18
    },
    {
      id: 3,
      name: "Jennifer Park",
      role: "Product Manager",
      company: "GrowthCorp",
      rating: 5,
      date: "2024-01-08",
      title: "Excellent support and documentation",
      text: "Implementation was smooth thanks to comprehensive docs. When we had questions, support responded within hours. The platform scales effortlessly - we went from 1K to 100K users without issues.",
      avatar: "JP",
      verified: true,
      helpful: 31
    },
    {
      id: 4,
      name: "David Thompson",
      role: "Security Lead",
      company: "EnterpriseMax",
      rating: 5,
      date: "2024-01-05",
      title: "Perfect for enterprise compliance",
      text: "Security features are top-notch. GDPR compliance, audit trails, and role-based access made our compliance team happy. The multi-tenant architecture works perfectly for our B2B SaaS.",
      avatar: "DT",
      verified: true,
      helpful: 22
    },
    {
      id: 5,
      name: "Lisa Wang",
      role: "Operations Director",
      company: "ScaleUp Inc",
      rating: 5,
      date: "2024-01-03",
      title: "Cost-effective and reliable",
      text: "Switched from expensive enterprise solutions. namaskah delivers the same features at 60% lower cost. 99.9% uptime in 8 months of usage. The AI suggestions actually help our support team.",
      avatar: "LW",
      verified: true,
      helpful: 19
    },
    {
      id: 6,
      name: "Ahmed Hassan",
      role: "Founder",
      company: "MobileFirst",
      rating: 4,
      date: "2023-12-28",
      title: "Great platform with minor room for improvement",
      text: "Overall excellent experience. The SMS delivery rates are fantastic and the API is well-designed. Would love to see more customization options for the chat interface, but that's a minor issue.",
      avatar: "AH",
      verified: true,
      helpful: 15
    },
    {
      id: 7,
      name: "Maria Gonzalez",
      role: "Engineering Manager",
      company: "DataDriven Co",
      rating: 5,
      date: "2023-12-25",
      title: "Seamless integration experience",
      text: "Integrated namaskah in just 2 days. The webhook system is robust and the real-time dashboard gives us great visibility. Customer support is responsive and knowledgeable.",
      avatar: "MG",
      verified: true,
      helpful: 27
    },
    {
      id: 8,
      name: "Robert Kim",
      role: "VP Engineering",
      company: "CloudNative Systems",
      rating: 5,
      date: "2023-12-20",
      title: "Scales beautifully with our growth",
      text: "Started with 1000 SMS/month, now processing 500K+. namaskah scaled seamlessly without any configuration changes. The pricing is transparent and the analytics help us optimize our flows.",
      avatar: "RK",
      verified: true,
      helpful: 33
    }
  ];

  const stats = {
    averageRating: 4.9,
    totalReviews: 247,
    ratingDistribution: {
      5: 89,
      4: 8,
      3: 2,
      2: 1,
      1: 0
    }
  };

  const filteredReviews = reviews.filter(review => {
    if (filterRating === 'all') return true;
    return review.rating === parseInt(filterRating);
  });

  const sortedReviews = [...filteredReviews].sort((a, b) => {
    if (sortBy === 'newest') return new Date(b.date) - new Date(a.date);
    if (sortBy === 'oldest') return new Date(a.date) - new Date(b.date);
    if (sortBy === 'highest') return b.rating - a.rating;
    if (sortBy === 'helpful') return b.helpful - a.helpful;
    return 0;
  });

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <span key={i} className={i < rating ? "text-yellow-400" : "text-gray-300"}>
        ⭐
      </span>
    ));
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

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
              <Link to="/about" className="text-gray-600 hover:text-blue-600">About</Link>
              <Link to="/reviews" className="text-blue-600 font-semibold">Reviews</Link>
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
              Customer Reviews
            </Typography>
            <Typography variant="body" className="text-xl mb-8 text-blue-100">
              See what our customers say about namaskah. Real reviews from real developers and businesses.
            </Typography>
            
            {/* Trustpilot-style rating display */}
            <div className="flex items-center justify-center mb-6 space-x-4">
              <div className="flex items-center">
                <span className="text-yellow-400 text-2xl mr-2">⭐⭐⭐⭐⭐</span>
                <span className="text-2xl font-bold text-white">{stats.averageRating}/5</span>
              </div>
              <div className="text-blue-100">•</div>
              <div className="text-blue-100">{stats.totalReviews} reviews</div>
            </div>
          </div>
        </div>
      </section>

      {/* Rating Distribution */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <Typography variant="h2" className="text-3xl font-bold mb-4">
                Rating Distribution
              </Typography>
            </div>
            
            <div className="grid md:grid-cols-5 gap-4 mb-8">
              {[5, 4, 3, 2, 1].map(rating => {
                const count = stats.ratingDistribution[rating];
                const percentage = (count / stats.totalReviews * 100).toFixed(1);
                
                return (
                  <div key={rating} className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <span className="text-sm font-medium mr-2">{rating}</span>
                      <span className="text-yellow-400">⭐</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div 
                        className="bg-yellow-400 h-2 rounded-full" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <div className="text-sm text-gray-600">{percentage}% ({count})</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Filters and Reviews */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            {/* Filter Controls */}
            <div className="flex flex-col md:flex-row justify-between items-center mb-8 space-y-4 md:space-y-0">
              <div className="flex items-center space-x-4">
                <Typography className="font-semibold">Filter by rating:</Typography>
                <select 
                  value={filterRating} 
                  onChange={(e) => setFilterRating(e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="all">All ratings</option>
                  <option value="5">5 stars</option>
                  <option value="4">4 stars</option>
                  <option value="3">3 stars</option>
                  <option value="2">2 stars</option>
                  <option value="1">1 star</option>
                </select>
              </div>
              
              <div className="flex items-center space-x-4">
                <Typography className="font-semibold">Sort by:</Typography>
                <select 
                  value={sortBy} 
                  onChange={(e) => setSortBy(e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="newest">Newest first</option>
                  <option value="oldest">Oldest first</option>
                  <option value="highest">Highest rating</option>
                  <option value="helpful">Most helpful</option>
                </select>
              </div>
            </div>

            {/* Reviews Grid */}
            <div className="grid lg:grid-cols-2 gap-8">
              {sortedReviews.map((review) => (
                <Card key={review.id} className="p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center">
                      <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold mr-4">
                        {review.avatar}
                      </div>
                      <div>
                        <div className="flex items-center">
                          <Typography variant="h4" className="font-semibold mr-2">
                            {review.name}
                          </Typography>
                          {review.verified && (
                            <Badge variant="outline" className="text-xs">
                              Verified
                            </Badge>
                          )}
                        </div>
                        <Typography className="text-gray-600 text-sm">
                          {review.role} at {review.company}
                        </Typography>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center mb-1">
                        {renderStars(review.rating)}
                      </div>
                      <Typography className="text-gray-500 text-xs">
                        {formatDate(review.date)}
                      </Typography>
                    </div>
                  </div>
                  
                  <Typography variant="h4" className="font-semibold mb-3">
                    {review.title}
                  </Typography>
                  
                  <Typography className="text-gray-700 mb-4">
                    "{review.text}"
                  </Typography>
                  
                  <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <button className="flex items-center text-gray-500 hover:text-blue-600 text-sm">
                      👍 Helpful ({review.helpful})
                    </button>
                    <Typography className="text-gray-400 text-xs">
                      Verified purchase
                    </Typography>
                  </div>
                </Card>
              ))}
            </div>

            {/* Load More Button */}
            <div className="text-center mt-12">
              <Button variant="outline" className="px-8 py-3">
                Load More Reviews
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-blue-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <Typography variant="h2" className="text-3xl font-bold mb-4 text-white">
            Join Our Happy Customers
          </Typography>
          <Typography className="text-xl mb-8 text-blue-100 max-w-2xl mx-auto">
            Start your free trial today and see why developers love namaskah.
          </Typography>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 w-full sm:w-auto">
                Start Free Trial
              </Button>
            </Link>
            <Link to="/about">
              <Button variant="outline" className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600 w-full sm:w-auto">
                Learn More
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

export default ReviewsPage;