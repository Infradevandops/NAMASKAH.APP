# Component API Reference

## Overview

This document provides comprehensive documentation for all namaskah frontend components, including their props, usage examples, and best practices. All components follow consistent patterns and are built with accessibility, performance, and developer experience in mind.

## Atomic Components

### Button

The Button component is the primary interactive element for user actions.

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `variant` | `'primary' \| 'secondary' \| 'outline' \| 'ghost' \| 'link'` | `'primary'` | No | Visual style variant of the button |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | No | Size of the button |
| `disabled` | `boolean` | `false` | No | Whether the button is disabled |
| `loading` | `boolean` | `false` | No | Shows loading spinner and disables interaction |
| `leftIcon` | `ReactNode` | `undefined` | No | Icon to display on the left side |
| `rightIcon` | `ReactNode` | `undefined` | No | Icon to display on the right side |
| `onClick` | `(event: MouseEvent) => void` | `undefined` | No | Click event handler |
| `type` | `'button' \| 'submit' \| 'reset'` | `'button'` | No | Button type attribute |
| `href` | `string` | `undefined` | No | URL for link buttons (renders as anchor) |
| `target` | `string` | `undefined` | No | Link target attribute |
| `rel` | `string` | `undefined` | No | Link rel attribute |
| `fullWidth` | `boolean` | `false` | No | Makes button take full width of container |
| `className` | `string` | `undefined` | No | Additional CSS classes |

#### Usage Examples

```jsx
import { Button } from '@/components/atoms/Button';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

// Basic button
<Button onClick={handleClick}>
  Click me
</Button>

// Button with icon
<Button leftIcon={<PlusIcon />} variant="primary">
  Add Item
</Button>

// Loading state
<Button loading variant="primary">
  Processing...
</Button>

// Link button
<Button href="/dashboard" variant="link">
  Go to Dashboard
</Button>

// Full width button
<Button fullWidth variant="outline" size="lg">
  Submit Form
</Button>

// Disabled state
<Button disabled variant="secondary">
  Cannot click
</Button>
```

#### Accessibility

- Always provide meaningful `onClick` handlers or `href` attributes
- Use `loading` state instead of disabling during async operations
- Ensure sufficient color contrast for all variants
- Keyboard navigation is automatically handled

#### Best Practices

- Use `variant="primary"` for primary actions
- Use `variant="outline"` for secondary actions
- Use `variant="ghost"` for subtle actions
- Use `variant="link"` for navigation
- Always provide loading states for async operations
- Use icons consistently (left for primary actions, right for secondary)

### Input

The Input component handles user text input with validation and accessibility features.

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `type` | `'text' \| 'email' \| 'password' \| 'number' \| 'tel' \| 'url' \| 'search'` | `'text'` | No | Input type |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | No | Size of the input |
| `disabled` | `boolean` | `false` | No | Whether the input is disabled |
| `error` | `string \| boolean` | `false` | No | Error message or boolean state |
| `placeholder` | `string` | `undefined` | No | Placeholder text |
| `label` | `string` | `undefined` | No | Label text (creates accessible label) |
| `required` | `boolean` | `false` | No | Whether the input is required |
| `value` | `string \| number` | `undefined` | No | Controlled value |
| `defaultValue` | `string \| number` | `undefined` | No | Default value for uncontrolled usage |
| `onChange` | `(value: string) => void` | `undefined` | No | Change event handler |
| `onBlur` | `(event: FocusEvent) => void` | `undefined` | No | Blur event handler |
| `onFocus` | `(event: FocusEvent) => void` | `undefined` | No | Focus event handler |
| `maxLength` | `number` | `undefined` | No | Maximum number of characters |
| `minLength` | `number` | `undefined` | No | Minimum number of characters |
| `pattern` | `string` | `undefined` | No | Validation pattern |
| `autoComplete` | `string` | `undefined` | No | Autocomplete attribute |
| `autoFocus` | `boolean` | `false` | No | Auto-focus on mount |
| `multiline` | `boolean` | `false` | No | Render as textarea |
| `rows` | `number` | `4` | No | Number of rows for textarea |
| `className` | `string` | `undefined` | No | Additional CSS classes |

#### Usage Examples

```jsx
import { Input } from '@/components/atoms/Input';

// Basic text input
<Input
  label="Username"
  placeholder="Enter your username"
  onChange={setUsername}
  required
/>

// Email input with validation
<Input
  type="email"
  label="Email Address"
  placeholder="user@example.com"
  error={emailError}
  onChange={setEmail}
  required
/>

// Password input
<Input
  type="password"
  label="Password"
  placeholder="Enter your password"
  onChange={setPassword}
  required
/>

// Number input
<Input
  type="number"
  label="Age"
  placeholder="Enter your age"
  min={13}
  max={120}
  onChange={setAge}
/>

// Multiline textarea
<Input
  label="Description"
  placeholder="Enter a description"
  multiline
  rows={6}
  onChange={setDescription}
/>

// Search input
<Input
  type="search"
  placeholder="Search for users..."
  onChange={setSearchQuery}
  leftIcon={<SearchIcon />}
/>
```

#### Validation Examples

```jsx
import { useState } from 'react';
import { Input } from '@/components/atoms/Input';

function ValidationExample() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    age: ''
  });

  const [errors, setErrors] = useState({});

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email) ? null : 'Please enter a valid email address';
  };

  const validatePassword = (password) => {
    if (password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
      return 'Password must contain uppercase, lowercase, and number';
    }
    return null;
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleBlur = (field, value) => {
    let error = null;

    switch (field) {
      case 'email':
        error = validateEmail(value);
        break;
      case 'password':
        error = validatePassword(value);
        break;
    }

    if (error) {
      setErrors(prev => ({ ...prev, [field]: error }));
    }
  };

  return (
    <form>
      <Input
        label="Email"
        type="email"
        value={formData.email}
        onChange={(value) => handleChange('email', value)}
        onBlur={(e) => handleBlur('email', e.target.value)}
        error={errors.email}
        required
      />

      <Input
        label="Password"
        type="password"
        value={formData.password}
        onChange={(value) => handleChange('password', value)}
        onBlur={(e) => handleBlur('password', e.target.value)}
        error={errors.password}
        required
      />
    </form>
  );
}
```

### Card

The Card component provides a flexible container for content with consistent styling.

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `variant` | `'default' \| 'outline' \| 'elevated'` | `'default'` | No | Visual style variant |
| `padding` | `'none' \| 'sm' \| 'md' \| 'lg' \| 'xl'` | `'md'` | No | Internal padding |
| `shadow` | `'none' \| 'sm' \| 'md' \| 'lg' \| 'xl'` | `'none'` | No | Shadow depth |
| `hover` | `boolean` | `false` | No | Enable hover effects |
| `onClick` | `(event: MouseEvent) => void` | `undefined` | No | Click event handler |
| `className` | `string` | `undefined` | No | Additional CSS classes |

#### Compound Components

```jsx
import { Card } from '@/components/atoms/Card';

// Using compound components
<Card>
  <Card.Header>
    <h3>Card Title</h3>
  </Card.Header>
  <Card.Content>
    <p>Card content goes here...</p>
  </Card.Content>
  <Card.Footer>
    <Button variant="outline">Cancel</Button>
    <Button variant="primary">Save</Button>
  </Card.Footer>
</Card>

// Interactive card
<Card
  hover
  onClick={handleCardClick}
  className="cursor-pointer"
>
  <Card.Content>
    <h4>Click me!</h4>
    <p>This entire card is clickable.</p>
  </Card.Content>
</Card>
```

## Molecule Components

### Modal

The Modal component provides overlay dialogs for important user interactions.

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `isOpen` | `boolean` | `false` | Yes | Whether the modal is open |
| `onClose` | `() => void` | `undefined` | Yes | Close event handler |
| `title` | `string` | `undefined` | No | Modal title |
| `size` | `'sm' \| 'md' \| 'lg' \| 'xl' \| 'fullscreen'` | `'md'` | No | Modal size |
| `backdrop` | `'click' \| 'static' \| 'none'` | `'click'` | No | Backdrop behavior |
| `position` | `'top' \| 'center' \| 'bottom'` | `'center'` | No | Modal position |

#### Usage Examples

```jsx
import { Modal } from '@/components/molecules/Modal';
import { useState } from 'react';

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

// Usage in component
function App() {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <Button onClick={() => setShowModal(true)}>
        Open Modal
      </Button>

      <ConfirmationModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onConfirm={() => {
          // Handle confirmation
          setShowModal(false);
        }}
      />
    </>
  );
}
```

### SearchBar

The SearchBar component provides a consistent search interface with filtering capabilities.

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `placeholder` | `string` | `'Search...'` | No | Placeholder text |
| `value` | `string` | `undefined` | No | Controlled search value |
| `onChange` | `(value: string) => void` | `undefined` | No | Change event handler |
| `onSearch` | `(query: string) => void` | `undefined` | No | Search event handler |
| `variant` | `'default' \| 'outline' \| 'filled'` | `'default'` | No | Visual style variant |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | No | Size of the search bar |
| `loading` | `boolean` | `false` | No | Shows loading state |
| `debounceMs` | `number` | `300` | No | Debounce delay for search |

#### Usage Examples

```jsx
import { SearchBar } from '@/components/molecules/SearchBar';
import { useState, useCallback } from 'react';

function UserSearch() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);

  const handleSearch = useCallback(async (searchQuery) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const searchResults = await searchUsers(searchQuery);
      setResults(searchResults);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div>
      <SearchBar
        placeholder="Search for users..."
        value={query}
        onChange={setQuery}
        onSearch={handleSearch}
        loading={loading}
        variant="outline"
        debounceMs={500}
      />

      {results.length > 0 && (
        <div className="search-results">
          {results.map(user => (
            <div key={user.id} className="user-result">
              {user.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### DataTable

The DataTable component provides a flexible table interface with sorting, filtering, and pagination.

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `data` | `array` | `[]` | Yes | Data array to display |
| `columns` | `array` | `[]` | Yes | Column configuration |
| `sortable` | `boolean` | `true` | No | Enable column sorting |
| `filterable` | `boolean` | `true` | No | Enable column filtering |
| `pagination` | `boolean` | `true` | No | Enable pagination |
| `selectable` | `boolean` | `false` | No | Enable row selection |
| `loading` | `boolean` | `false` | No | Shows loading state |
| `pageSize` | `number` | `10` | No | Number of items per page |

#### Column Configuration

```jsx
const columns = [
  {
    key: 'name',
    label: 'Name',
    sortable: true,
    filterable: true,
    width: '200px',
    render: (value, row) => (
      <div className="flex items-center">
        <Avatar src={row.avatar} size="sm" />
        <span className="ml-2">{value}</span>
      </div>
    )
  },
  {
    key: 'email',
    label: 'Email',
    sortable: true,
    filterable: true
  },
  {
    key: 'role',
    label: 'Role',
    filterable: true,
    options: ['admin', 'user', 'moderator']
  },
  {
    key: 'actions',
    label: 'Actions',
    render: (value, row) => (
      <div className="flex gap-2">
        <Button size="sm" variant="outline">
          Edit
        </Button>
        <Button size="sm" variant="ghost">
          Delete
        </Button>
      </div>
    )
  }
];
```

## Best Practices

### Component Composition

```jsx
// ✅ Good: Using compound components
<Card>
  <Card.Header>
    <h3>Settings</h3>
  </Card.Header>
  <Card.Content>
    <Input label="Name" />
    <Input label="Email" type="email" />
  </Card.Content>
  <Card.Footer>
    <Button variant="outline">Cancel</Button>
    <Button variant="primary">Save</Button>
  </Card.Footer>
</Card>

// ❌ Avoid: Mixing different component systems
<div className="card">
  <div className="card-header">
    <h3>Settings</h3>
  </div>
  <div className="card-content">
    <input className="input" placeholder="Name" />
    <input className="input" type="email" placeholder="Email" />
  </div>
  <div className="card-footer">
    <button className="btn-outline">Cancel</button>
    <button className="btn-primary">Save</button>
  </div>
</div>
```

### Form Handling

```jsx
// ✅ Good: Controlled components with validation
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

    // Validate form
    const newErrors = validateForm(formData);
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      await submitForm(formData);
      // Success handling
    } catch (error) {
      setErrors({ submit: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Input
        label="Name"
        value={formData.name}
        onChange={(value) => {
          setFormData(prev => ({ ...prev, name: value }));
          // Clear error on change
          if (errors.name) {
            setErrors(prev => ({ ...prev, name: undefined }));
          }
        }}
        error={errors.name}
        required
      />

      <Input
        label="Email"
        type="email"
        value={formData.email}
        onChange={(value) => {
          setFormData(prev => ({ ...prev, email: value }));
          if (errors.email) {
            setErrors(prev => ({ ...prev, email: undefined }));
          }
        }}
        error={errors.email}
        required
      />

      <Input
        label="Message"
        value={formData.message}
        onChange={(value) => {
          setFormData(prev => ({ ...prev, message: value }));
        }}
        error={errors.message}
        multiline
        rows={4}
      />

      <Button type="submit" loading={loading}>
        {loading ? 'Sending...' : 'Send Message'}
      </Button>
    </form>
  );
}
```

### Accessibility

```jsx
// ✅ Good: Proper accessibility implementation
function AccessibleForm() {
  const [errors, setErrors] = useState({});

  return (
    <form
      onSubmit={handleSubmit}
      role="form"
      aria-label="Contact form"
    >
      <Input
        label="Email address"
        type="email"
        required
        aria-describedby={errors.email ? "email-error" : undefined}
        error={errors.email}
      />
      {errors.email && (
        <div id="email-error" role="alert" className="error-message">
          {errors.email}
        </div>
      )}

      <Button type="submit">
        Submit form
      </Button>
    </form>
  );
}

// ✅ Good: Keyboard navigation
function KeyboardAccessibleModal({ isOpen, onClose }) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      aria-labelledby="modal-title"
      aria-describedby="modal-description"
    >
      <Modal.Header>
        <h2 id="modal-title">Confirm Action</h2>
      </Modal.Header>
      <Modal.Content>
        <p id="modal-description">
          This action cannot be undone. Are you sure you want to continue?
        </p>
      </Modal.Content>
      <Modal.Footer>
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleConfirm}>
          Confirm
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
```

## Migration Guide

### From HTML/CSS to Components

```jsx
// ❌ Before: Raw HTML
<div class="card">
  <div class="card-header">
    <h3>Card Title</h3>
  </div>
  <div class="card-body">
    <input type="text" class="form-control" placeholder="Name">
    <button class="btn btn-primary">Submit</button>
  </div>
</div>

// ✅ After: Component-based
<Card>
  <Card.Header>
    <h3>Card Title</h3>
  </Card.Header>
  <Card.Content>
    <Input label="Name" placeholder="Name" />
    <Button variant="primary">Submit</Button>
  </Card.Content>
</Card>
```

### From Class Components to Hooks

```jsx
// ❌ Before: Class component
class ContactForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = { name: '', email: '' };
  }

  handleSubmit = (e) => {
    e.preventDefault();
    // Handle form submission
  };

  render() {
    return (
      <form onSubmit={this.handleSubmit}>
        <input
          value={this.state.name}
          onChange={(e) => this.setState({ name: e.target.value })}
        />
        <button type="submit">Submit</button>
      </form>
    );
  }
}

// ✅ After: Functional component with hooks
function ContactForm() {
  const [formData, setFormData] = useState({ name: '', email: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    // Handle form submission
  };

  return (
    <form onSubmit={handleSubmit}>
      <Input
        label="Name"
        value={formData.name}
        onChange={(value) => setFormData(prev => ({ ...prev, name: value }))}
      />
      <Button type="submit">Submit</Button>
    </form>
  );
}
```

This comprehensive API reference provides everything developers need to effectively use namaskah components. For more examples and interactive documentation, refer to the Storybook stories at `/storybook`.