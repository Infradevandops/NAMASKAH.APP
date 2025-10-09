import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Icon, Typography, Card } from '../atoms';
import { FormField, PasswordStrengthMeter } from '../molecules';
import { useAuth } from '../../hooks/useAuth';
import { useNotification } from '../../contexts/NotificationContext';

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    phone: '',
    agreeToTerms: false,
    subscribeNewsletter: false
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [step, setStep] = useState(1);
  
  const { register } = useAuth();
  const { addNotification } = useNotification();
  const navigate = useNavigate();

  const validateStep1 = () => {
    const newErrors = {};
    
    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    }
    
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    }
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors = {};
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    if (!formData.agreeToTerms) {
      newErrors.agreeToTerms = 'You must agree to the terms and conditions';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (step === 1) {
      if (validateStep1()) {
        setStep(2);
      }
      return;
    }
    
    if (!validateStep2()) {
      return;
    }
    
    setLoading(true);
    
    try {
      const result = await register(
        formData.email, 
        formData.password, 
        formData.firstName, 
        formData.lastName
      );
      
      if (result.success) {
        addNotification('Registration successful! Please login with your credentials.', 'success');
        navigate('/login');
      } else {
        setErrors({ submit: result.error || 'Registration failed. Please try again.' });
      }
    } catch (err) {
      setErrors({ submit: 'Registration failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleSocialRegister = (provider) => {
    console.log(`Register with ${provider}`);
    // Implement social registration
  };

  const getPasswordStrength = (password) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    return strength;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      {/* Back to Home Link */}
      <div className="absolute top-4 left-4">
        <Link to="/" className="flex items-center text-blue-600 hover:text-blue-800">
          ← Back to Home
        </Link>
      </div>
      
      <div className="max-w-md w-full">
        <Card padding="lg" shadow="lg">
          {/* Header */}
          <div className="text-center mb-8">
            <Link to="/" className="flex justify-center mb-4">
              <h1 className="text-3xl font-bold text-blue-600">namaskah</h1>
            </Link>
            <div className="mx-auto h-12 w-12 bg-blue-600 rounded-full flex items-center justify-center mb-4">
              <Icon name="phone" className="text-white" size="lg" />
            </div>
            <Typography variant="h2" className="text-gray-900">
              Create your account
            </Typography>
            <Typography variant="body2" className="text-gray-600 mt-2">
              Join namaskah and start communicating
            </Typography>
          </div>

          {/* Progress Indicator */}
          <div className="mb-8">
            <div className="flex items-center">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full ${
                step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
              }`}>
                {step > 1 ? <Icon name="check" size="sm" /> : '1'}
              </div>
              <div className={`flex-1 h-1 mx-2 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />
              <div className={`flex items-center justify-center w-8 h-8 rounded-full ${
                step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
              }`}>
                2
              </div>
            </div>
            <div className="flex justify-between mt-2">
              <Typography variant="caption" className="text-gray-500">
                Personal Info
              </Typography>
              <Typography variant="caption" className="text-gray-500">
                Security
              </Typography>
            </div>
          </div>

          {/* Error Message */}
          {errors.submit && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-center">
              <Icon name="warning" className="text-red-500 mr-2" size="sm" />
              <Typography variant="body2" className="text-red-700">
                {errors.submit}
              </Typography>
            </div>
          )}

          {/* Social Registration */}
          {step === 1 && (
            <>
              <div className="space-y-3 mb-6">
                <Button
                  variant="outline"
                  fullWidth
                  onClick={() => handleSocialRegister('google')}
                  startIcon={<Icon name="mail" size="sm" />}
                >
                  Sign up with Google
                </Button>
                <Button
                  variant="outline"
                  fullWidth
                  onClick={() => handleSocialRegister('github')}
                  startIcon={<Icon name="settings" size="sm" />}
                >
                  Sign up with GitHub
                </Button>
              </div>

              {/* Divider */}
              <div className="relative mb-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">Or sign up with email</span>
                </div>
              </div>
            </>
          )}

          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {step === 1 && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    label="First Name"
                    type="text"
                    name="firstName"
                    value={formData.firstName}
                    onChange={handleChange}
                    placeholder="John"
                    error={errors.firstName}
                    required
                    autoComplete="given-name"
                  />
                  
                  <FormField
                    label="Last Name"
                    type="text"
                    name="lastName"
                    value={formData.lastName}
                    onChange={handleChange}
                    placeholder="Doe"
                    error={errors.lastName}
                    required
                    autoComplete="family-name"
                  />
                </div>
                
                <FormField
                  label="Email Address"
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="john@example.com"
                  error={errors.email}
                  required
                  autoComplete="email"
                />
                
                <FormField
                  label="Phone Number (Optional)"
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="+1 (555) 123-4567"
                  autoComplete="tel"
                />
              </>
            )}

            {step === 2 && (
              <>
                <FormField
                  label="Password"
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Create a strong password"
                  error={errors.password}
                  required
                  autoComplete="new-password"
                />
                
                {formData.password && (
                  <PasswordStrengthMeter 
                    password={formData.password}
                    strength={getPasswordStrength(formData.password)}
                  />
                )}
                
                <FormField
                  label="Confirm Password"
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Confirm your password"
                  error={errors.confirmPassword}
                  required
                  autoComplete="new-password"
                />

                {/* Terms and Conditions */}
                <div className="space-y-3">
                  <label className="flex items-start">
                    <input
                      type="checkbox"
                      name="agreeToTerms"
                      checked={formData.agreeToTerms}
                      onChange={handleChange}
                      className="mt-1 rounded border-gray-300 text-red-600 focus:ring-red-500"
                    />
                    <div className="ml-2">
                      <Typography variant="body2" className="text-gray-700">
                        I agree to the{' '}
                        <button type="button" className="text-red-600 hover:text-red-500 font-medium">
                          Terms of Service
                        </button>
                        {' '}and{' '}
                        <button type="button" className="text-red-600 hover:text-red-500 font-medium">
                          Privacy Policy
                        </button>
                      </Typography>
                      {errors.agreeToTerms && (
                        <Typography variant="caption" className="text-red-600">
                          {errors.agreeToTerms}
                        </Typography>
                      )}
                    </div>
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="subscribeNewsletter"
                      checked={formData.subscribeNewsletter}
                      onChange={handleChange}
                      className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                    />
                    <Typography variant="body2" className="ml-2 text-gray-700">
                      Subscribe to our newsletter for updates and tips
                    </Typography>
                  </label>
                </div>
              </>
            )}

            {/* Navigation Buttons */}
            <div className="flex space-x-3 mt-6">
              {step === 2 && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep(1)}
                  className="flex-1"
                >
                  Back
                </Button>
              )}
              
              <Button
                type="submit"
                loading={loading}
                className="flex-1"
              >
                {step === 1 ? 'Continue' : loading ? 'Creating Account...' : 'Create Account'}
              </Button>
            </div>
          </form>

          {/* Sign In Link */}
          <div className="mt-6 text-center">
            <Typography variant="body2" className="text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="text-blue-600 hover:text-blue-500 font-medium">
                Sign in
              </Link>
            </Typography>
          </div>
        </Card>

        {/* Footer */}
        <div className="mt-8 text-center">
          <Typography variant="caption" className="text-gray-500">
            By creating an account, you agree to our{' '}
            <Link to="/about" className="text-blue-600 hover:text-blue-800">Terms of Service</Link>
            {' '}and{' '}
            <Link to="/about" className="text-blue-600 hover:text-blue-800">Privacy Policy</Link>
          </Typography>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;