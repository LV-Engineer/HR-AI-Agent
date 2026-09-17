import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'

// jsdom doesn't implement scrollIntoView; components that auto-scroll would crash without this stub.
Element.prototype.scrollIntoView = () => {}

afterEach(() => {
  cleanup()
})
