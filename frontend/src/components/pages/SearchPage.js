import React, { useState, useEffect, useCallback } from 'react';
import { AdvancedSearchBar, SearchResults } from '../molecules';
import { Button, Icon } from '../atoms';

const SearchPage = () => {
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentQuery, setCurrentQuery] = useState('');
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedResults, setSelectedResults] = useState([]);

  // Mock data for demonstration
  const mockResults = [
    {
      id: 1,
      title: 'Advanced React Components Guide',
      description: 'A comprehensive guide to building advanced React components with hooks and context.',
      type: 'file',
      fileType: 'pdf',
      size: 2048576,
      path: '/documents/guides',
      author: 'John Doe',
      createdAt: '2024-01-15T10:30:00Z',
      preview: { type: 'document', url: '/preview/1.jpg' }
    },
    {
      id: 2,
      title: 'JavaScript Best Practices',
      description: 'Modern JavaScript development patterns and best practices for 2024.',
      type: 'file',
      fileType: 'docx',
      size: 1536000,
      path: '/documents/tutorials',
      author: 'Jane Smith',
      createdAt: '2024-01-10T14:20:00Z',
      preview: { type: 'document', url: '/preview/2.jpg' }
    },
    {
      id: 3,
      title: 'API Documentation',
      description: 'Complete API documentation for the search service endpoints.',
      type: 'file',
      fileType: 'json',
      size: 512000,
      path: '/api/docs',
      author: 'API Team',
      createdAt: '2024-01-08T09:15:00Z',
      preview: { type: 'document', url: '/preview/3.jpg' }
    },
    {
      id: 4,
      title: 'Design System Components',
      description: 'UI component library documentation and usage examples.',
      type: 'folder',
      size: 10485760,
      path: '/design-system',
      author: 'Design Team',
      createdAt: '2024-01-05T16:45:00Z'
    },
    {
      id: 5,
      title: 'Search Algorithm Implementation',
      description: 'Technical documentation for the advanced search algorithm implementation.',
      type: 'file',
      fileType: 'md',
      size: 256000,
      path: '/technical/algorithms',
      author: 'Tech Lead',
      createdAt: '2024-01-03T11:30:00Z'
    }
  ];

  // Filter configuration
  const filterOptions = [
    {
      key: 'type',
      label: 'Content Type',
      multiple: true,
      options: [
        { value: 'file', label: 'Files', count: 15 },
        { value: 'folder', label: 'Folders', count: 8 },
        { value: 'image', label: 'Images', count: 12 },
        { value: 'document', label: 'Documents', count: 25 }
      ]
    },
    {
      key: 'fileType',
      label: 'File Format',
      multiple: true,
      options: [
        { value: 'pdf', label: 'PDF', count: 10 },
        { value: 'docx', label: 'Word Document', count: 8 },
        { value: 'txt', label: 'Text File', count: 15 },
        { value: 'json', label: 'JSON', count: 5 },
        { value: 'md', label: 'Markdown', count: 12 }
      ]
    },
    {
      key: 'author',
      label: 'Author',
      multiple: true,
      options: [
        { value: 'john-doe', label: 'John Doe', count: 8 },
        { value: 'jane-smith', label: 'Jane Smith', count: 12 },
        { value: 'api-team', label: 'API Team', count: 5 },
        { value: 'design-team', label: 'Design Team', count: 7 },
        { value: 'tech-lead', label: 'Tech Lead', count: 3 }
      ]
    },
    {
      key: 'size',
      label: 'File Size',
      multiple: false,
      options: [
        { value: 'small', label: 'Small (< 1MB)', count: 20 },
        { value: 'medium', label: 'Medium (1-10MB)', count: 15 },
        { value: 'large', label: 'Large (> 10MB)', count: 5 }
      ]
    }
  ];

  // Sort options
  const sortOptions = [
    { value: 'relevance', label: 'Relevance' },
    { value: 'date-desc', label: 'Newest First' },
    { value: 'date-asc', label: 'Oldest First' },
    { value: 'name-asc', label: 'Name A-Z' },
    { value: 'name-desc', label: 'Name Z-A' },
    { value: 'size-desc', label: 'Largest First' },
    { value: 'size-asc', label: 'Smallest First' }
  ];

  // Simulate search API call
  const performSearch = useCallback(async (searchData) => {
    setLoading(true);
    setError(null);
    
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Mock search logic
      let filteredResults = [...mockResults];
      
      // Apply text search
      if (searchData.query || searchData.originalQuery) {
        const query = (searchData.query || searchData.originalQuery).toLowerCase();
        filteredResults = filteredResults.filter(result => 
          result.title.toLowerCase().includes(query) ||
          result.description.toLowerCase().includes(query) ||
          result.author.toLowerCase().includes(query)
        );
      }
      
      // Apply filters
      if (searchData.filters) {
        Object.entries(searchData.filters).forEach(([key, value]) => {
          if (value && (Array.isArray(value) ? value.length > 0 : true)) {
            filteredResults = filteredResults.filter(result => {
              const resultValue = result[key];
              if (Array.isArray(value)) {
                return value.includes(resultValue);
              }
              return resultValue === value;
            });
          }
        });
      }
      
      // Apply advanced filters
      if (searchData.advanced) {
        const { dateFrom, dateTo, fileType, author, minSize, maxSize } = searchData.advanced;
        
        if (dateFrom || dateTo) {
          filteredResults = filteredResults.filter(result => {
            const resultDate = new Date(result.createdAt);
            const fromDate = dateFrom ? new Date(dateFrom) : new Date('1900-01-01');
            const toDate = dateTo ? new Date(dateTo) : new Date();
            return resultDate >= fromDate && resultDate <= toDate;
          });
        }
        
        if (fileType) {
          filteredResults = filteredResults.filter(result => 
            result.fileType === fileType
          );
        }
        
        if (author) {
          filteredResults = filteredResults.filter(result => 
            result.author.toLowerCase().includes(author.toLowerCase())
          );
        }
        
        if (minSize) {
          filteredResults = filteredResults.filter(result => 
            result.size >= parseInt(minSize) * 1024
          );
        }
        
        if (maxSize) {
          filteredResults = filteredResults.filter(result => 
            result.size <= parseInt(maxSize) * 1024
          );
        }
      }
      
      // Apply sorting
      if (searchData.sort) {
        filteredResults.sort((a, b) => {
          switch (searchData.sort) {
            case 'date-desc':
              return new Date(b.createdAt) - new Date(a.createdAt);
            case 'date-asc':
              return new Date(a.createdAt) - new Date(b.createdAt);
            case 'name-asc':
              return a.title.localeCompare(b.title);
            case 'name-desc':
              return b.title.localeCompare(a.title);
            case 'size-desc':
              return b.size - a.size;
            case 'size-asc':
              return a.size - b.size;
            default:
              return 0; // relevance - keep original order
          }
        });
      }
      
      setSearchResults(filteredResults);
      setTotalCount(filteredResults.length);
      setCurrentQuery(searchData.originalQuery || searchData.query || '');
      setCurrentPage(1);
      

      
    } catch (err) {
      setError('Failed to perform search. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle search
  const handleSearch = (searchData) => {
    performSearch(searchData);
  };

  // Handle filter changes
  const handleFilterChange = (filters) => {
    // Filters are handled in the search function
    console.log('Filters changed:', filters);
  };

  // Handle result click
  const handleResultClick = (result) => {
    console.log('Result clicked:', result);
    // In a real app, this would navigate to the result or open a preview
  };

  // Handle page change
  const handlePageChange = (page) => {
    setCurrentPage(page);
    // In a real app, this would trigger a new search with pagination
  };

  // Handle result selection
  const handleResultSelect = (selectedIds) => {
    setSelectedResults(selectedIds);
  };

  // Bulk actions
  const handleBulkDownload = () => {
    console.log('Bulk download:', selectedResults);
    // Implement bulk download logic
  };

  const handleBulkDelete = () => {
    if (window.confirm(`Are you sure you want to delete ${selectedResults.length} items?`)) {
      console.log('Bulk delete:', selectedResults);
      // Implement bulk delete logic
      setSelectedResults([]);
    }
  };

  // Extract highlight terms from query
  const getHighlightTerms = () => {
    if (!currentQuery) return [];
    return currentQuery.split(' ').filter(term => term.length > 2);
  };

  // Initial search on component mount
  useEffect(() => {
    performSearch({ query: '', filters: {}, sort: 'relevance', advanced: {} });
  }, [performSearch]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Advanced Search</h1>
          <p className="text-gray-600">
            Search through documents, files, and content with powerful filtering options.
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <AdvancedSearchBar
            placeholder="Search for documents, files, or content..."
            onSearch={handleSearch}
            onFilterChange={handleFilterChange}
            filters={filterOptions}
            sortOptions={sortOptions}
            showFilters={true}
            showSort={true}
            showAdvanced={true}
            className="bg-white rounded-lg shadow-sm"
          />
        </div>

        {/* Bulk Actions */}
        {selectedResults.length > 0 && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Icon name="check" size="sm" className="text-blue-600" />
                <span className="text-sm font-medium text-blue-900">
                  {selectedResults.length} item{selectedResults.length !== 1 ? 's' : ''} selected
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleBulkDownload}
                  className="border-blue-300 text-blue-700 hover:bg-blue-100"
                >
                  <Icon name="download" size="sm" className="mr-1" />
                  Download
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleBulkDelete}
                  className="border-red-300 text-red-700 hover:bg-red-100"
                >
                  <Icon name="trash" size="sm" className="mr-1" />
                  Delete
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedResults([])}
                  className="text-gray-600"
                >
                  Clear selection
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Search Results */}
        <div className="bg-white rounded-lg shadow-sm">
          <SearchResults
            results={searchResults}
            loading={loading}
            error={error}
            searchQuery={currentQuery}
            totalCount={totalCount}
            currentPage={currentPage}
            pageSize={10}
            onPageChange={handlePageChange}
            onResultClick={handleResultClick}
            onResultSelect={handleResultSelect}
            selectedResults={selectedResults}
            showSelection={true}
            showPreview={true}
            highlightTerms={getHighlightTerms()}
            className="p-6"
          />
        </div>

        {/* Search Tips */}
        <div className="mt-8 bg-gray-100 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Search Tips</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-800 mb-2">Basic Search</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Use quotes for exact phrases: "advanced search"</li>
                <li>• Use - to exclude words: javascript -framework</li>
                <li>• Use wildcards: react*</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-800 mb-2">Advanced Features</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Filter by file type, author, or date range</li>
                <li>• Save frequently used searches</li>
                <li>• Export search results and configurations</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchPage;