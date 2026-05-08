/**
 * NBG Chart Configuration for MCP Server Chart
 *
 * Pre-configured chart settings that match NBG brand guidelines.
 * Use these configurations when generating charts via mcp-server-chart.
 */

const NBG_CHART_CONFIG = {
  // NBG Color Palette
  colors: {
    // Primary chart colors (in order of use)
    chartSequence: [
      '#00ADBF',  // Cyan (primary)
      '#003841',  // Dark Teal
      '#007B85',  // NBG Teal
      '#939793',  // Medium Gray
      '#BEC1BE',  // Light Gray
      '#00DFF8',  // Bright Cyan
    ],

    // Single-series colors
    primary: '#00ADBF',
    secondary: '#003841',
    tertiary: '#007B85',

    // Semantic colors
    positive: '#73AF3C',   // Success Green
    negative: '#AA0028',   // Alert Red
    neutral: '#939793',    // Medium Gray
    highlight: '#00DFF8',  // Bright Cyan

    // Status colors (for indicators)
    status: {
      deepRed: '#CB0030',
      red: '#F60037',
      orange: '#FF7F1A',
      yellow: '#FFDC00',
      green: '#5D8D2F',
      brightGreen: '#90DC48',
    },

    // Segment colors
    segments: {
      business: '#0D90FF',
      corporate: '#73AF3C',
      premium: '#D9A757',
      private: '#AA0028',
    },

    // Background
    background: '#FFFFFF',
    gridLines: '#E5E5E5',
  },

  // Typography
  fonts: {
    primary: 'Aptos',
    fallback: 'Arial, Helvetica, sans-serif',
    title: {
      family: 'Aptos',
      size: 14,
      weight: 'bold',
      color: '#003841',
    },
    axis: {
      family: 'Aptos',
      size: 10,
      color: '#595959',
    },
    legend: {
      family: 'Aptos',
      size: 10,
      color: '#202020',
    },
    dataLabel: {
      family: 'Aptos',
      size: 10,
      weight: 'bold',
      color: '#202020',
    },
  },

  // Chart-specific configurations
  charts: {
    // pie is remapped to doughnut per brand rules — NEVER use pie charts
    pie: {
      colors: ['#00ADBF', '#003841', '#007B85', '#939793', '#BEC1BE', '#00DFF8'],
      showPercent: true,
      showLabels: true,
      legendPosition: 'right',
      innerRadius: 50,  // remapped to doughnut (same as donut config)
    },

    donut: {
      colors: ['#00ADBF', '#003841', '#007B85', '#939793', '#BEC1BE', '#00DFF8'],
      showPercent: true,
      showLabels: true,
      legendPosition: 'right',
      innerRadius: 50,  // Hole size percentage
    },

    bar: {
      colors: ['#00ADBF', '#003841', '#007B85', '#939793', '#BEC1BE', '#00DFF8'],
      barWidth: 0.7,
      gapWidth: 30,
      showDataLabels: true,
      dataLabelPosition: 'outside',
      gridLines: true,
    },

    column: {
      colors: ['#00ADBF', '#003841', '#007B85', '#939793', '#BEC1BE', '#00DFF8'],
      barWidth: 0.7,
      gapWidth: 30,
      showDataLabels: true,
      dataLabelPosition: 'outside',
      gridLines: true,
    },

    line: {
      colors: ['#00ADBF', '#003841', '#007B85', '#939793', '#BEC1BE', '#00DFF8'],
      lineWidth: 3,
      showMarkers: true,
      smooth: true,
      showDataLabels: false,
      gridLines: true,
    },

    area: {
      colors: ['#00ADBF', '#003841', '#007B85', '#939793', '#BEC1BE', '#00DFF8'],
      opacity: 0.3,
      lineWidth: 2,
      showMarkers: false,
      gridLines: true,
    },

    waterfall: {
      positiveColor: '#00ADBF',
      negativeColor: '#AA0028',
      totalColor: '#003841',
      showDataLabels: true,
    },
  },

  // Axis configuration
  axis: {
    x: {
      showTitle: true,
      titleColor: '#003841',
      labelColor: '#595959',
      labelRotation: 0,
      gridLines: false,
    },
    y: {
      showTitle: true,
      titleColor: '#003841',
      labelColor: '#595959',
      gridLines: true,
      gridLineColor: '#E5E5E5',
    },
  },

  // Legend configuration
  legend: {
    show: true,
    position: 'top',  // 'top', 'bottom', 'left', 'right'
    fontFamily: 'Aptos',
    fontSize: 10,
    fontColor: '#202020',
  },
};

/**
 * Generate MCP chart configuration for a specific chart type
 */
function getNBGChartConfig(chartType, options = {}) {
  const baseConfig = NBG_CHART_CONFIG.charts[chartType] || NBG_CHART_CONFIG.charts.bar;

  return {
    ...baseConfig,
    ...options,
    colors: options.colors || baseConfig.colors,
    title: {
      ...NBG_CHART_CONFIG.fonts.title,
      text: options.title || '',
    },
    font: NBG_CHART_CONFIG.fonts.primary,
    backgroundColor: NBG_CHART_CONFIG.colors.background,
  };
}

/**
 * Get color array for specific number of data points
 */
function getNBGColors(count) {
  const colors = NBG_CHART_CONFIG.colors.chartSequence;
  if (count <= colors.length) {
    return colors.slice(0, count);
  }
  // Repeat colors if more needed
  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length]);
  }
  return result;
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    NBG_CHART_CONFIG,
    getNBGChartConfig,
    getNBGColors,
  };
}

// Export for browser/ES modules
if (typeof window !== 'undefined') {
  window.NBG_CHART_CONFIG = NBG_CHART_CONFIG;
  window.getNBGChartConfig = getNBGChartConfig;
  window.getNBGColors = getNBGColors;
}
