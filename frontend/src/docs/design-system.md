# namaskah Design System

## Overview

The namaskah Design System provides a comprehensive set of design tokens, components, and guidelines to ensure consistent user experience across the application. This system is built on modern design principles and follows accessibility best practices.

## Design Principles

### 1. **User-Centered Design**
- Every design decision prioritizes user needs and goals
- Interfaces should be intuitive and require minimal cognitive load
- Users should be able to accomplish their tasks efficiently

### 2. **Accessibility First**
- WCAG 2.1 AA compliance as minimum standard
- Inclusive design for users with disabilities
- Keyboard navigation support for all interactive elements
- High contrast ratios and readable typography

### 3. **Consistency**
- Standardized spacing, colors, and typography
- Predictable interaction patterns
- Unified visual language across all components

### 4. **Performance**
- Optimized for fast loading and smooth interactions
- Minimal bundle size impact
- Efficient rendering and state management

## Design Tokens

### Colors

#### Primary Palette
```css
--color-primary-50: #f0f9ff;
--color-primary-100: #e0f2fe;
--color-primary-200: #bae6fd;
--color-primary-300: #7dd3fc;
--color-primary-400: #38bdf8;
--color-primary-500: #0ea5e9;  /* Primary brand color */
--color-primary-600: #0284c7;
--color-primary-700: #0369a1;
--color-primary-800: #075985;
--color-primary-900: #0c4a6e;
```

#### Semantic Colors
```css
--color-success-50: #f0fdf4;
--color-success-500: #22c55e;
--color-success-900: #14532d;

--color-warning-50: #fffbeb;
--color-warning-500: #f59e0b;
--color-warning-900: #78350f;

--color-error-50: #fef2f2;
--color-error-500: #ef4444;
--color-error-900: #7f1d1d;

--color-info-50: #f0f9ff;
--color-info-500: #3b82f6;
--color-info-900: #1e3a8a;
```

#### Neutral Colors
```css
--color-gray-50: #f9fafb;
--color-gray-100: #f3f4f6;
--color-gray-200: #e5e7eb;
--color-gray-300: #d1d5db;
--color-gray-400: #9ca3af;
--color-gray-500: #6b7280;
--color-gray-600: #4b5563;
--color-gray-700: #374151;
--color-gray-800: #1f2937;
--color-gray-900: #111827;
```

### Typography

#### Font Families
```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
--font-mono: 'Fira Code', 'Monaco', 'Consolas', monospace;
```

#### Font Sizes
```css
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
--text-5xl: 3rem;      /* 48px */
```

#### Font Weights
```css
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

#### Line Heights
```css
--leading-tight: 1.25;
--leading-snug: 1.375;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
--leading-loose: 2;
```

### Spacing

#### Base Unit System
```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
--space-24: 6rem;     /* 96px */
```

### Border Radius
```css
--radius-none: 0;
--radius-sm: 0.125rem;   /* 2px */
--radius-base: 0.25rem;  /* 4px */
--radius-md: 0.375rem;   /* 6px */
--radius-lg: 0.5rem;     /* 8px */
--radius-xl: 0.75rem;    /* 12px */
--radius-2xl: 1rem;      /* 16px */
--radius-full: 9999px;
```

### Shadows
```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-base: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
--shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
```

## Component Library

### Atomic Components

#### Button
The Button component is the primary interactive element for user actions.

**Props:**
- `variant`: `'primary' | 'secondary' | 'outline' | 'ghost' | 'link'`
- `size`: `'sm' | 'md' | 'lg'`
- `disabled`: `boolean`
- `loading`: `boolean`
- `leftIcon`: `ReactNode`
- `rightIcon`: `ReactNode`
- `onClick`: `function`

**Usage:**
```jsx
import { Button } from '@/components/atoms/Button';

// Primary button
<Button variant="primary" onClick={handleSubmit}>
  Submit Form
</Button>

// Button with icon
<Button variant="outline" leftIcon={<PlusIcon />} size="lg">
  Add Item
</Button>

// Loading state
<Button loading variant="primary">
  Processing...
</Button>
```

#### Input
The Input component handles user text input with validation and accessibility features.

**Props:**
- `type`: `'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search'`
- `size`: `'sm' | 'md' | 'lg'`
- `disabled`: `boolean`
- `error`: `string | boolean`
- `placeholder`: `string`
- `label`: `string`
- `required`: `boolean`
- `onChange`: `function`
- `onBlur`: `function`

**Usage:**
```jsx
import { Input } from '@/components/atoms/Input';

// Basic input
<Input
  label="Email Address"
  type="email"
  placeholder="Enter your email"
  onChange={handleEmailChange}
/>

// Input with error state
<Input
  label="Password"
  type="password"
  error="Password must be at least 8 characters"
  onChange={handlePasswordChange}
/>
```

#### Card
The Card component provides a flexible container for content with consistent styling.

**Props:**
- `variant`: `'default' | 'outline' | 'elevated'`
- `padding`: `'none' | 'sm' | 'md' | 'lg' | 'xl'`
- `shadow`: `'none' | 'sm' | 'md' | 'lg' | 'xl'`
- `hover`: `boolean`
- `onClick`: `function`

**Usage:**
```jsx
import { Card } from '@/components/atoms/Card';

// Basic card
<Card padding="lg" shadow="md">
  <h3>Card Title</h3>
  <p>Card content goes here...</p>
</Card>

// Interactive card
<Card
  hover
  onClick={handleCardClick}
  className="cursor-pointer"
>
  <Card.Header>
    <h3>Interactive Card</h3>
  </Card.Header>
  <Card.Content>
    <p>Click me to perform an action</p>
  </Card.Content>
</Card>
```

### Molecule Components

#### Modal
The Modal component provides overlay dialogs for important user interactions.

**Props:**
- `isOpen`: `boolean`
- `onClose`: `function`
- `title`: `string`
- `size`: `'sm' | 'md' | 'lg' | 'xl' | 'fullscreen'`
- `backdrop`: `'click' | 'static' | 'none'`
- `position`: `'top' | 'center' | 'bottom'`

**Usage:**
```jsx
import { Modal } from '@/components/molecules/Modal';

function ConfirmationModal({ isOpen, onClose, onConfirm }) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Confirm Action"
      size="md"
    >
      <Modal.Header>
        <h2>Are you sure?</h2>
      </Modal.Header>
      <Modal.Content>
        <p>This action cannot be undone.</p>
      </Modal.Content>
      <Modal.Footer>
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="primary" onClick={onConfirm}>
          Confirm
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
```

#### SearchBar
The SearchBar component provides a consistent search interface with filtering capabilities.

**Props:**
- `placeholder`: `string`
- `value`: `string`
- `onChange`: `function`
- `onSearch`: `function`
- `variant`: `'default' | 'outline' | 'filled'`
- `size`: `'sm' | 'md' | 'lg'`
- `loading`: `boolean`

**Usage:**
```jsx
import { SearchBar } from '@/components/molecules/SearchBar';

function UserSearch() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSearch = async (searchQuery) => {
    setLoading(true);
    try {
      const results = await searchUsers(searchQuery);
      // Handle results
    } finally {
      setLoading(false);
    }
  };

  return (
    <SearchBar
      placeholder="Search users..."
      value={query}
      onChange={setQuery}
      onSearch={handleSearch}
      loading={loading}
      variant="outline"
    />
  );
}
```

#### DataTable
The DataTable component provides a flexible table interface with sorting, filtering, and pagination.

**Props:**
- `data`: `array`
- `columns`: `array`
- `sortable`: `boolean`
- `filterable`: `boolean`
- `pagination`: `boolean`
- `selectable`: `boolean`
- `loading`: `boolean`

**Usage:**
```jsx
import { DataTable } from '@/components/molecules/DataTable';

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'email', label: 'Email', sortable: true },
  { key: 'role', label: 'Role', filterable: true },
  { key: 'actions', label: 'Actions' }
];

function UserTable({ users }) {
  return (
    <DataTable
      data={users}
      columns={columns}
      sortable
      filterable
      pagination
      selectable
    />
  );
}
```

### Organism Components

#### Header
The Header component provides consistent navigation and user context across the application.

**Props:**
- `user`: `object`
- `onLogin`: `function`
- `onLogout`: `function`
- `onSearch`: `function`
- `navigation`: `array`

**Usage:**
```jsx
import { Header } from '@/components/organisms/Header';

function AppHeader() {
  const { user, logout } = useAuth();

  const navigation = [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Messages', href: '/messages' },
    { label: 'Settings', href: '/settings' }
  ];

  return (
    <Header
      user={user}
      onLogout={logout}
      navigation={navigation}
    />
  );
}
```

## Usage Patterns

### Form Handling
```jsx
import { useState } from 'react';
import { Button, Input, Card } from '@/components';

function ContactForm() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await submitForm(formData);
      // Success handling
    } catch (error) {
      setErrors(error.response.data.errors);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  return (
    <Card padding="lg">
      <form onSubmit={handleSubmit}>
        <Input
          label="Name"
          value={formData.name}
          onChange={(value) => handleChange('name', value)}
          error={errors.name}
          required
        />

        <Input
          label="Email"
          type="email"
          value={formData.email}
          onChange={(value) => handleChange('email', value)}
          error={errors.email}
          required
        />

        <Input
          label="Message"
          value={formData.message}
          onChange={(value) => handleChange('message', value)}
          error={errors.message}
          multiline
          rows={4}
        />

        <Button
          type="submit"
          loading={loading}
          disabled={loading}
        >
          Send Message
        </Button>
      </form>
    </Card>
  );
}
```

### Loading States
```jsx
import { Button, Card } from '@/components';

function LoadingExample() {
  const [loading, setLoading] = useState(false);

  const handleAction = async () => {
    setLoading(true);
    try {
      await performAction();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <Button
        onClick={handleAction}
        loading={loading}
      >
        {loading ? 'Processing...' : 'Start Action'}
      </Button>
    </Card>
  );
}
```

### Error Handling
```jsx
import { useState } from 'react';
import { Card, Button } from '@/components';

function ErrorExample() {
  const [error, setError] = useState(null);

  const handleRetry = () => {
    setError(null);
    // Retry logic
  };

  if (error) {
    return (
      <Card variant="outline" className="error-state">
        <h3>Something went wrong</h3>
        <p>{error.message}</p>
        <Button onClick={handleRetry} variant="outline">
          Try Again
        </Button>
      </Card>
    );
  }

  return (
    <Card>
      <p>Content loaded successfully</p>
    </Card>
  );
}
```

## Accessibility Guidelines

### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Tab order should follow logical flow
- Focus indicators must be visible
- Skip links for main content areas

### Screen Reader Support
- Proper ARIA labels and descriptions
- Semantic HTML structure
- Alternative text for images
- Form labels and error messages

### Color and Contrast
- Minimum 4.5:1 contrast ratio for normal text
- Minimum 3:1 contrast ratio for large text
- No reliance on color alone for information
- High contrast mode support

### Motion and Animation
- Respect `prefers-reduced-motion` setting
- Provide alternatives for animated content
- Smooth, purposeful animations only
- No auto-playing content

## Performance Guidelines

### Bundle Size
- Tree-shake unused exports
- Lazy load non-critical components
- Optimize images and assets
- Minimize third-party dependencies

### Rendering Performance
- Use React.memo for expensive components
- Implement virtualization for large lists
- Debounce expensive operations
- Use CSS containment where appropriate

### Network Performance
- Implement proper caching strategies
- Minimize API calls with batching
- Use pagination for large datasets
- Implement optimistic updates

## Browser Support

### Modern Browsers
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Graceful Degradation
- Progressive enhancement approach
- Fallbacks for unsupported features
- Clear messaging for limited functionality

## Contributing

### Adding New Components
1. Follow atomic design principles
2. Include comprehensive tests
3. Add Storybook stories
4. Document all props and usage
5. Ensure accessibility compliance

### Design Token Updates
1. Update token definitions
2. Update component implementations
3. Test across all breakpoints
4. Verify accessibility compliance

### Testing Requirements
- Unit tests for all components
- Integration tests for complex flows
- Accessibility tests with axe-core
- Visual regression tests
- Performance benchmarks

---

This design system is living documentation that evolves with the application. Always refer to the latest Storybook stories for current component implementations and usage examples.