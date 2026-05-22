import '@testing-library/jest-dom'

// Mock ResizeObserver for Recharts
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.ResizeObserver = ResizeObserverMock

// Mock DOMRect for Recharts
if (!global.DOMRect) {
  global.DOMRect = class DOMRect {
    x = 0
    y = 0
    width = 100
    height = 100
    top = 0
    right = 100
    bottom = 100
    left = 0
    constructor(x = 0, y = 0, width = 100, height = 100) {
      this.x = x
      this.y = y
      this.width = width
      this.height = height
      this.top = y
      this.right = x + width
      this.bottom = y + height
      this.left = x
    }
  }
}
