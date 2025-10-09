import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import SearchBar from '../molecules/SearchBar';

const Header = ({ user, onLogout, onSearch }) => {
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const handleProfileToggle = () => {
    setIsProfileMenuOpen(!isProfileMenuOpen);
  };
  
  const handleMobileMenuToggle = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };
  
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Link to="/dashboard" className="text-xl font-bold text-blue-600 hover:text-blue-800">
                namaskah
              </Link>
            </div>
          </div>
          
          {/* Navigation */}
          <nav className="hidden md:flex space-x-8">
            <Link to="/dashboard" className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium">
              Dashboard
            </Link>
            <Link to="/chat" className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium">
              Chat
            </Link>
            <Link to="/numbers" className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium">
              Numbers
            </Link>
            <Link to="/billing" className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium">
              Billing
            </Link>
          </nav>
          
          {/* Search Bar - Hidden on mobile */}
          <div className="hidden lg:flex flex-1 max-w-lg mx-8">
            <SearchBar 
              placeholder="Search messages, numbers, users..."
              onSearch={onSearch}
              showButton={false}
            />
          </div>
          
          {/* User Profile Menu */}
          <div className="relative">
            <button
              onClick={handleProfileToggle}
              className="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <span className="sr-only">Open user menu</span>
              <div className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center">
                <span className="text-sm font-medium text-gray-700">
                  {user?.name?.charAt(0) || 'U'}
                </span>
              </div>
            </button>
            
            {isProfileMenuOpen && (
              <div className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
                <div className="py-1">
                  <Link to="/dashboard" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                    Your Profile
                  </Link>
                  <Link to="/dashboard" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                    Settings
                  </Link>
                  <button
                    onClick={onLogout}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button 
              onClick={handleMobileMenuToggle}
              className="text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
            >
              <span className="sr-only">Open main menu</span>
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isMobileMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
              </svg>
            </button>
          </div>
        </div>
        
        {/* Mobile menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t border-gray-200">
              {/* Mobile Search */}
              <div className="px-3 py-2">
                <SearchBar 
                  placeholder="Search..."
                  onSearch={onSearch}
                  showButton={false}
                />
              </div>
              
              {/* Mobile Navigation */}
              <Link to="/dashboard" className="text-gray-700 hover:bg-gray-100 block px-3 py-2 rounded-md text-base font-medium">
                Dashboard
              </Link>
              <Link to="/chat" className="text-gray-700 hover:bg-gray-100 block px-3 py-2 rounded-md text-base font-medium">
                Chat
              </Link>
              <Link to="/numbers" className="text-gray-700 hover:bg-gray-100 block px-3 py-2 rounded-md text-base font-medium">
                Numbers
              </Link>
              <Link to="/billing" className="text-gray-700 hover:bg-gray-100 block px-3 py-2 rounded-md text-base font-medium">
                Billing
              </Link>
              
              {/* Mobile Profile Menu */}
              <div className="border-t border-gray-200 pt-4">
                <div className="flex items-center px-3">
                  <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                    <span className="text-sm font-medium text-gray-700">
                      {user?.name?.charAt(0) || 'U'}
                    </span>
                  </div>
                  <div className="ml-3">
                    <div className="text-base font-medium text-gray-800">{user?.name || 'User'}</div>
                    <div className="text-sm font-medium text-gray-500">{user?.email}</div>
                  </div>
                </div>
                <div className="mt-3 space-y-1">
                  <Link to="/dashboard" className="block px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100">
                    Your Profile
                  </Link>
                  <Link to="/dashboard" className="block px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100">
                    Settings
                  </Link>
                  <button
                    onClick={onLogout}
                    className="block w-full text-left px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100"
                  >
                    Sign out
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;