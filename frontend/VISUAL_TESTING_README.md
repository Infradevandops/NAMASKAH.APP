# Visual Testing Guide

This guide explains how to use the automated visual regression testing setup for the namaskah frontend.

## Overview

The visual testing setup includes:
- **Storybook Test Runner** for automated testing of stories
- **Chromatic** for visual regression testing and review
- **Accessibility Testing** with axe-core
- **Cross-browser Testing** for consistent rendering
- **Performance Testing** with Lighthouse

## Prerequisites

1. **Node.js** 16+ and npm installed
2. **Storybook** configured and running
3. **Chromatic account** (for visual regression testing)

## Installation

All required packages are already installed:

```bash
npm install  # Installs all testing dependencies
```

## Available Scripts

### Development Testing

```bash
# Run all visual tests
npm run test:visual

# Run accessibility tests only
npm run test:a11y

# Run smoke tests (quick validation)
npm run test:smoke

# Run Storybook test runner
npm run test:storybook
```

### CI/CD Testing

```bash
# Run visual tests in CI mode (optimized for CI)
npm run test:visual:ci

# Run Chromatic for visual regression testing
npm run chromatic

# Run Chromatic in CI mode (auto-accept changes)
npm run chromatic:ci
```

### Coverage and Analysis

```bash
# Run tests with coverage
npm run test:coverage

# Run tests in CI mode with coverage
npm run test:ci
```

## Configuration

### Visual Testing Configuration

The visual testing configuration is located in `.storybook/visual-testing.config.js`:

- **Viewports**: Mobile (375px), Tablet (768px), Desktop (1280px), Wide (1920px)
- **Failure Threshold**: 1% difference tolerance
- **Baseline Branch**: `main` for comparison
- **Included Stories**: All atoms, molecules, organisms, and pages
- **Excluded Stories**: Playground and Examples stories

### Accessibility Configuration

- **Rules**: Color contrast, image alt text, button names, link names
- **Standards**: WCAG 2.1 AA compliance
- **Automated**: Runs on all component stories
- **Reporting**: Detailed violation reports with suggestions

## Running Tests

### Local Development

1. **Start Storybook**:
   ```bash
   npm run storybook
   ```

2. **Run Visual Tests**:
   ```bash
   npm run test:visual
   ```

3. **Run Accessibility Tests**:
   ```bash
   npm run test:a11y
   ```

### CI/CD Pipeline

The tests are configured to run automatically in CI with:

- **Parallel Execution**: 4 workers for faster testing
- **Headless Mode**: Optimized for CI environments
- **Retry Logic**: Automatic retries for flaky tests
- **Artifacts**: Test results and screenshots saved

## Test Results

### Visual Regression Results

- **Screenshots**: Saved in `test-results/screenshots/`
- **Diff Images**: Show differences between baseline and current
- **Reports**: HTML reports with detailed comparisons
- **Artifacts**: Available in CI for review

### Accessibility Results

- **Violations**: Listed with severity levels
- **Suggestions**: Automated fix recommendations
- **Standards**: WCAG 2.1 AA compliance reports
- **Export**: JSON and HTML formats available

## Chromatic Integration

### Setup

1. **Create Chromatic Account**: Sign up at [chromatic.com](https://chromatic.com)
2. **Get Project Token**: Available in your project settings
3. **Set Environment Variable**:
   ```bash
   export CHROMATIC_PROJECT_TOKEN=your_token_here
   ```

### Usage

```bash
# Run Chromatic visual testing
npm run chromatic

# Run in CI mode (auto-accept changes)
npm run chromatic:ci
```

### Features

- **Visual Review**: Side-by-side comparison of changes
- **Auto-Accept**: Automatically accept non-breaking changes
- **Branch Comparison**: Compare against baseline branch
- **Component Isolation**: Test components in isolation
- **Team Collaboration**: Share reviews with team members

## Custom Test Matchers

The setup includes custom Jest matchers for component testing:

```javascript
// Accessibility testing
expect(component).toBeAccessible();

// Component props validation
expect(component).toHaveValidProps({ variant: 'primary' });

// Component state validation
expect(component).toHaveState({ isLoading: false });

// Component styling validation
expect(component).toHaveStyle({ color: 'red' });

// Component children validation
expect(component).toHaveChildren(2);
```

## Test Utilities

Global test utilities are available for all tests:

```javascript
// Create mock props
const mockProps = global.testMatchers.createMockProps('Button', {
  variant: 'primary',
  size: 'large'
});

// Create mock state
const mockState = global.testMatchers.createMockState({
  isLoading: true,
  error: null
});

// Create mock event handlers
const mockHandlers = global.testMatchers.createMockHandlers({
  onClick: jest.fn(),
  onChange: jest.fn()
});
```

## Troubleshooting

### Common Issues

1. **Storybook Not Running**:
   ```bash
   npm run storybook  # Ensure Storybook is running
   ```

2. **Chromatic Token Missing**:
   ```bash
   export CHROMATIC_PROJECT_TOKEN=your_token_here
   ```

3. **Test Timeouts**:
   - Increase timeout in configuration
   - Check network connectivity
   - Verify Storybook is accessible

4. **Flaky Tests**:
   - Enable retry logic in CI
   - Check for animations affecting screenshots
   - Verify consistent test environment

### Debug Mode

Run tests in debug mode for detailed logging:

```bash
npm run test:debug
```

## Best Practices

### Writing Testable Stories

1. **Consistent Props**: Use consistent prop values across stories
2. **No Random Data**: Avoid random or dynamic content
3. **Stable State**: Ensure stories render in a stable state
4. **Clear Names**: Use descriptive story names
5. **Documentation**: Include comprehensive story documentation

### Visual Testing

1. **Baseline Images**: Review baseline images before approving
2. **Thresholds**: Set appropriate failure thresholds
3. **Viewports**: Test on all required viewports
4. **Animations**: Disable animations for consistent screenshots
5. **Loading States**: Test loading and error states

### Accessibility Testing

1. **WCAG Compliance**: Follow WCAG 2.1 AA guidelines
2. **Color Contrast**: Ensure sufficient color contrast ratios
3. **Keyboard Navigation**: Test keyboard accessibility
4. **Screen Readers**: Verify screen reader compatibility
5. **Focus Management**: Check focus indicators and management

## CI/CD Integration

### GitHub Actions

The visual testing is integrated with GitHub Actions:

- **Pull Request Checks**: Automatic visual regression testing
- **Branch Protection**: Require visual tests to pass
- **Artifact Collection**: Screenshots and reports saved
- **Status Checks**: Visual testing status reported

### Required Secrets

Add these secrets to your GitHub repository:

- `CHROMATIC_PROJECT_TOKEN`: Your Chromatic project token
- `CHROMATIC_AUTO_ACCEPT_CHANGES`: Set to `true` for auto-accept
- `CHROMATIC_EXIT_ZERO_ON_CHANGES`: Set to `true` for CI compatibility

## Performance Benchmarks

The setup includes performance testing with:

- **Lighthouse Scores**: Performance, accessibility, best practices, SEO
- **Core Web Vitals**: LCP, FID, CLS measurements
- **Bundle Analysis**: Component and page bundle sizes
- **Load Times**: Component rendering performance

## Contributing

When adding new components:

1. **Create Stories**: Add comprehensive Storybook stories
2. **Include Tests**: Add visual and accessibility tests
3. **Update Documentation**: Update this guide if needed
4. **Review Changes**: Use Chromatic to review visual changes

## Support

For issues with visual testing:

1. **Check Configuration**: Verify all configuration files
2. **Review Logs**: Check test runner logs for errors
3. **Update Dependencies**: Ensure all packages are up to date
4. **Community Support**: Check Storybook and Chromatic documentation

---

*This visual testing setup ensures consistent, accessible, and performant user interfaces across all components and pages.*