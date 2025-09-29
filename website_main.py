import React, { useState, useEffect } from 'react';
import { ChevronRight, Shield, Zap, TrendingUp, Users, DollarSign, Star, Play, ArrowRight, Check, X } from 'lucide-react';

// Main Landing Page Component
const TrustGuardWebsite = () => {
  const [activeTab, setActiveTab] = useState('home');
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleEmailSubmit = (e) => {
    e.preventDefault();
    setIsSubmitted(true);
    // In production, this would send to your email service
    setTimeout(() => setIsSubmitted(false), 3000);
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-sm border-b border-gray-200 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">TrustGuard</span>
            </div>
            
            <div className="hidden md:flex items-center space-x-8">
              <button 
                onClick={() => setActiveTab('features')}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                Features
              </button>
              <button 
                onClick={() => setActiveTab('pricing')}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                Pricing
              </button>
              <button 
                onClick={() => setActiveTab('investors')}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                For Investors
              </button>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                Install Extension
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Content based on active tab */}
      {activeTab === 'home' && <HomePage setActiveTab={setActiveTab} email={email} setEmail={setEmail} handleEmailSubmit={handleEmailSubmit} isSubmitted={isSubmitted} />}
      {activeTab === 'features' && <FeaturesPage />}
      {activeTab === 'pricing' && <PricingPage />}
      {activeTab === 'investors' && <InvestorsPage />}
    </div>
  );
};

// Home Page Component
const HomePage = ({ setActiveTab, email, setEmail, handleEmailSubmit, isSubmitted }) => {
  return (
    <>
      {/* Hero Section */}
      <section className="pt-24 pb-16 bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800 mb-6">
                <Zap className="w-4 h-4 mr-2" />
                AI-Powered eBay Protection
              </div>
              
              <h1 className="text-4xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">
                Never Get 
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600"> Scammed</span> on eBay Again
              </h1>
              
              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                TrustGuard's AI instantly analyzes any eBay listing, detects scams, calculates profit potential, and finds arbitrage opportunities. Protect yourself and make money with every purchase.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <button className="bg-blue-600 text-white px-8 py-4 rounded-lg hover:bg-blue-700 transition-colors text-lg font-semibold flex items-center">
                  Install Free Extension
                  <ChevronRight className="w-5 h-5 ml-2" />
                </button>
                <button className="border border-gray-300 text-gray-700 px-8 py-4 rounded-lg hover:bg-gray-50 transition-colors text-lg font-semibold flex items-center">
                  <Play className="w-5 h-5 mr-2" />
                  Watch Demo
                </button>
              </div>
              
              <div className="flex items-center space-x-6 text-sm text-gray-500">
                <div className="flex items-center">
                  <div className="flex -space-x-2">
                    <div className="w-8 h-8 rounded-full bg-gray-300"></div>
                    <div className="w-8 h-8 rounded-full bg-gray-400"></div>
                    <div className="w-8 h-8 rounded-full bg-gray-500"></div>
                  </div>
                  <span className="ml-2">50,000+ protected users</span>
                </div>
                <div className="flex items-center">
                  <Star className="w-4 h-4 text-yellow-400 fill-current" />
                  <span className="ml-1">4.9/5 rating</span>
                </div>
              </div>
            </div>
            
            <div className="relative">
              <div className="bg-white rounded-2xl shadow-2xl p-6 transform rotate-3">
                <div className="bg-gradient-to-r from-green-400 to-blue-500 rounded-xl p-4 text-white mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm opacity-90">Trust Score</span>
                    <span className="text-xs opacity-75">Verified in 247ms</span>
                  </div>
                  <div className="text-3xl font-bold mb-1">92/100</div>
                  <div className="text-sm">✅ SAFE TO BUY</div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Market Value:</span>
                    <span className="font-semibold">$420</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Your Profit:</span>
                    <span className="font-semibold text-green-600">$120</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Time to Sell:</span>
                    <span className="font-semibold">12 days</span>
                  </div>
                </div>
                
                <div className="mt-4 p-3 bg-green-50 rounded-lg">
                  <div className="text-sm text-green-800">
                    ✅ Seller: 99.2% feedback, 4+ years
                  </div>
                  <div className="text-sm text-green-800">
                    ✅ Price within market range (+8%)
                  </div>
                </div>
              </div>
              
              {/* Floating elements */}
              <div className="absolute -top-4 -right-4 bg-yellow-400 text-yellow-900 px-3 py-1 rounded-full text-sm font-semibold animate-bounce">
                $2.3M+ Protected
              </div>
              <div className="absolute -bottom-4 -left-4 bg-purple-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                99.2% Accuracy
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl lg:text-4xl font-bold text-gray-900 mb-2">$2.3M+</div>
              <div className="text-gray-600">Protected from Scams</div>
            </div>
            <div>
              <div className="text-3xl lg:text-4xl font-bold text-gray-900 mb-2">50K+</div>
              <div className="text-gray-600">Active Users</div>
            </div>
            <div>
              <div className="text-3xl lg:text-4xl font-bold text-gray-900 mb-2">99.2%</div>
              <div className="text-gray-600">Detection Accuracy</div>
            </div>
            <div>
              <div className="text-3xl lg:text-4xl font-bold text-gray-900 mb-2">247ms</div>
              <div className="text-gray-600">Avg Response Time</div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Protection in 3 Simple Steps
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our AI instantly analyzes any eBay listing and gives you everything you need to make smart, safe purchases.
            </p>
          </div>
          
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Shield className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-4">Install Extension</h3>
              <p className="text-gray-600">
                One-click install from Chrome Web Store. Works instantly on any eBay listing page.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Zap className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold mb-4">AI Analysis</h3>
              <p className="text-gray-600">
                Our AI instantly scans seller history, price patterns, and market data in under 250ms.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <TrendingUp className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold mb-4">Make Money</h3>
              <p className="text-gray-600">
                Get instant buy/avoid recommendations plus profit opportunities and arbitrage alerts.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Email Signup */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
            Join 50,000+ Protected Users
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Get early access to new features and exclusive profit opportunities.
          </p>
          
          <form onSubmit={handleEmailSubmit} className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="flex-1 px-4 py-3 rounded-lg text-gray-900"
              required
            />
            <button
              type="submit"
              disabled={isSubmitted}
              className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors disabled:opacity-50"
            >
              {isSubmitted ? 'Subscribed! ✓' : 'Get Updates'}
            </button>
          </form>
        </div>
      </section>
    </>
  );
};

// Features Page
const FeaturesPage = () => {
  const features = [
    {
      icon: Shield,
      title: "Instant Scam Detection",
      description: "AI analyzes seller patterns, pricing anomalies, and listing quality to detect potential scams in real-time.",
      benefits: ["99.2% accuracy", "Sub-250ms response", "Continuous learning"]
    },
    {
      icon: TrendingUp,
      title: "Profit Analysis", 
      description: "Calculate exact profit potential, market value, and selling time estimates for any item.",
      benefits: ["Real market data", "ROI calculations", "Time-to-sell predictions"]
    },
    {
      icon: Zap,
      title: "Arbitrage Opportunities",
      description: "Find profitable items to flip across eBay, Amazon, Facebook Marketplace, and more.",
      benefits: ["Cross-platform scanning", "Automated alerts", "Profit margin analysis"]
    },
    {
      icon: Users,
      title: "Seller Intelligence",
      description: "Deep analysis of seller history, feedback patterns, and account authenticity.",
      benefits: ["Feedback verification", "Account age analysis", "Risk pattern detection"]
    }
  ];

  return (
    <div className="pt-24">
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
              Powerful Features for Smart Shopping
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Everything you need to shop safely, identify profit opportunities, and make money on eBay.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-12">
            {features.map((feature, index) => (
              <div key={index} className="bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-6">
                  <feature.icon className="w-6 h-6 text-blue-600" />
                </div>
                
                <h3 className="text-2xl font-bold text-gray-900 mb-4">{feature.title}</h3>
                <p className="text-gray-600 mb-6 leading-relaxed">{feature.description}</p>
                
                <ul className="space-y-2">
                  {feature.benefits.map((benefit, idx) => (
                    <li key={idx} className="flex items-center text-sm text-gray-700">
                      <Check className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                      {benefit}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

// Pricing Page
const PricingPage = () => {
  const plans = [
    {
      name: "Free",
      price: "$0",
      period: "forever",
      features: [
        "10 verifications per day",
        "Basic trust scoring", 
        "Community support",
        "Chrome extension"
      ],
      limitations: [
        "No advanced analytics",
        "No arbitrage alerts",
        "No seller tools"
      ],
      cta: "Start Free",
      popular: false
    },
    {
      name: "Pro",
      price: "$19.99",
      period: "month",
      features: [
        "Unlimited verifications",
        "Advanced AI analysis",
        "Arbitrage opportunities",
        "Seller tools & AI listing generation",
        "Photo enhancement",
        "Priority support",
        "Mobile app access"
      ],
      limitations: [],
      cta: "Start Free Trial",
      popular: true
    },
    {
      name: "Enterprise",
      price: "$199.99", 
      period: "month",
      features: [
        "Everything in Pro",
        "API access",
        "Custom integrations",
        "White-label options", 
        "Advanced analytics dashboard",
        "Dedicated support",
        "Custom training"
      ],
      limitations: [],
      cta: "Contact Sales",
      popular: false
    }
  ];

  return (
    <div className="pt-24">
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Choose the plan that fits your needs. Upgrade or downgrade anytime.
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {plans.map((plan, index) => (
              <div key={index} className={`relative bg-white p-8 rounded-2xl shadow-lg border-2 ${plan.popular ? 'border-blue-500' : 'border-gray-200'}`}>
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <div className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                      Most Popular
                    </div>
                  </div>
                )}
                
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <div className="mb-4">
                    <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                    <span className="text-gray-600">/{plan.period}</span>
                  </div>
                </div>

                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start">
                      <Check className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                  {plan.limitations.map((limitation, idx) => (
                    <li key={idx} className="flex items-start">
                      <X className="w-5 h-5 text-gray-400 mr-3 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-500">{limitation}</span>
                    </li>
                  ))}
                </ul>

                <button className={`w-full py-3 px-4 rounded-lg font-semibold transition-colors ${
                  plan.popular 
                    ? 'bg-blue-600 text-white hover:bg-blue-700' 
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                }`}>
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>

          <div className="text-center mt-12">
            <p className="text-gray-600 mb-4">All plans include 30-day money-back guarantee</p>
            <p className="text-sm text-gray-500">
              Questions? <button className="text-blue-600 hover:underline">Contact our sales team</button>
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

// Investors Page
const InvestorsPage = () => {
  return (
    <div className="pt-24">
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
              Investment Opportunity
            </h1>
            <p className="text-xl text-gray-600">
              Join us in building the future of e-commerce trust and intelligence.
            </p>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Market Opportunity</h2>
            
            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <div>
                <h3 className="text-lg font-semibold mb-4">Total Addressable Market</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Global E-commerce GMV:</span>
                    <span className="font-semibold">$5.8T</span>
                  </div>
                  <div className="flex justify-between">
                    <span>eBay Annual GMV:</span>
                    <span className="font-semibold">$87B</span>
                  </div>
                  <div className="flex justify-between">
                    <span>eBay Active Users:</span>
                    <span className="font-semibold">182M</span>
                  </div>
                  <div className="flex justify-between border-t pt-2 font-bold">
                    <span>Our Target Market:</span>
                    <span>$2.1B</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold mb-4">Current Traction</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Active Users:</span>
                    <span className="font-semibold">50,000+</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Monthly Revenue:</span>
                    <span className="font-semibold">$125K</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Growth Rate:</span>
                    <span className="font-semibold">25% MoM</span>
                  </div>
                  <div className="flex justify-between border-t pt-2 font-bold">
                    <span>Valuation:</span>
                    <span>$50M</span>
                  </div>
                </div>
              </div>
            </div>

            <h3 className="text-lg font-semibold mb-4">Comparable Companies</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Company</th>
                    <th className="text-left py-2">Exit Value</th>
                    <th className="text-left py-2">Revenue Multiple</th>
                    <th className="text-left py-2">Notes</th>
                  </tr>
                </thead>
                <tbody className="space-y-1">
                  <tr className="border-b">
                    <td className="py-2">Honey</td>
                    <td className="py-2 font-semibold">$4.0B</td>
                    <td className="py-2">40x</td>
                    <td className="py-2 text-gray-600">Acquired by PayPal</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-2">Capital One Shopping</td>
                    <td className="py-2 font-semibold">$2.5B</td>
                    <td className="py-2">25x</td>
                    <td className="py-2 text-gray-600">Price comparison</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-2">InvisibleHand</td>
                    <td className="py-2 font-semibold">$200M</td>
                    <td className="py-2">20x</td>
                    <td className="py-2 text-gray-600">Acquired by Yahoo</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white text-center">
            <h2 className="text-2xl font-bold mb-4">Ready to Invest?</h2>
            <p className="text-blue-100 mb-6">
              We're raising $5M Series A to accelerate growth and expand globally.
            </p>
            <button className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
              Request Investor Deck
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default TrustGuardWebsite;
