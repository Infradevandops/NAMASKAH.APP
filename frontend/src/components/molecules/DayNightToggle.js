import React from 'react';

const DayNightToggle = ({ darkMode, toggleDarkMode }) => {
  return (
    <button
      onClick={toggleDarkMode}
      aria-label="Toggle day and night mode"
      style={{
        backgroundColor: darkMode ? '#333' : '#eee',
        color: darkMode ? '#eee' : '#333',
        border: 'none',
        padding: '8px 16px',
        borderRadius: '20px',
        cursor: 'pointer',
        fontWeight: 'bold',
        transition: 'background-color 0.3s ease, color 0.3s ease',
      }}
    >
      {darkMode ? '🌙 Night' : '☀️ Day'}
    </button>
  );
};

export default DayNightToggle;
