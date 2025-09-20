/// <reference types="cypress" />

describe('Bldr Empire v2 - Query E2E Tests', () => {
  beforeEach(() => {
    // Visit the application
    cy.visit('http://localhost:3000')
    
    // Wait for the app to load
    cy.get('[data-testid="app-loaded"]', { timeout: 10000 }).should('be.visible')
  })

  it('successfully submits a query and shows progress', () => {
    // Navigate to query tab
    cy.get('[data-testid="query-tab"]').click()
    
    // Enter query text
    cy.get('[data-testid="query-input"]')
      .type('Проверь фото на СП31 + смета ГЭСН Екатеринбург')
    
    // Upload a sample photo (we'll use a mock file for testing)
    cy.get('[data-testid="file-upload"]').selectFile({
      contents: Cypress.Buffer.from('mock image content'),
      fileName: 'site.jpg',
      mimeType: 'image/jpeg'
    })
    
    // Select a project (mock selection)
    cy.get('[data-testid="project-selector"]').select('LSR Sample Project')
    
    // Submit the query
    cy.get('[data-testid="submit-query"]').click()
    
    // Check that progress steps are displayed
    cy.get('[data-testid="progress-steps"]', { timeout: 30000 })
      .should('be.visible')
      .find('[data-testid="progress-step"]')
      .should('have.length.at.least', 4)
    
    // Wait for parse step to complete
    cy.get('[data-testid="parse-step"]', { timeout: 60000 })
      .should('have.class', 'completed')
    
    // Wait for plan step to complete
    cy.get('[data-testid="plan-step"]', { timeout: 60000 })
      .should('have.class', 'completed')
    
    // Check parse tab content
    cy.get('[data-testid="parse-tab"]').click()
    cy.get('[data-testid="parse-result"]')
      .should('contain.text', 'qc+finance')
      .and('contain.text', 'СП31')
      .and('contain.text', 'ГЭСН')
    
    // Check plan tab content
    cy.get('[data-testid="plan-tab"]').click()
    cy.get('[data-testid="plan-result"]')
      .should('contain.text', 'qc_compliance')
      .and('contain.text', 'analyst')
      .and('contain.text', 'chief_engineer')
      .and('contain.text', 'vl_analyze')
      .and('contain.text', 'calc_estimate')
      .and('contain.text', 'gen_docx')
    
    // Check responses tab content
    cy.get('[data-testid="responses-tab"]').click()
    cy.get('[data-testid="responses-result"]')
      .should('contain.text', '[Source:')
      .and('not.contain.text', 'предположим')
    
    // Check final tab content
    cy.get('[data-testid="final-tab"]').click()
    cy.get('[data-testid="final-result"]')
      .should('contain.text', '[Source:')
      .and('not.contain.text', 'предположим')
    
    // Check that download button is available
    cy.get('[data-testid="download-zip"]')
      .should('be.visible')
      .and('be.enabled')
  })

  it('handles file upload errors gracefully', () => {
    // Navigate to query tab
    cy.get('[data-testid="query-tab"]').click()
    
    // Enter query text
    cy.get('[data-testid="query-input"]')
      .type('Анализ фото site.jpg на SanPiN')
    
    // Try to upload an invalid file
    cy.get('[data-testid="file-upload"]').selectFile({
      contents: Cypress.Buffer.from('invalid content'),
      fileName: 'invalid.txt',
      mimeType: 'text/plain'
    })
    
    // Check for error message
    cy.get('[data-testid="error-toast"]', { timeout: 10000 })
      .should('be.visible')
      .and('contain.text', 'VL error')
  })

  it('shows queue status correctly', () => {
    // Navigate to queue tab
    cy.get('[data-testid="queue-tab"]').click()
    
    // Check that queue table is displayed
    cy.get('[data-testid="queue-table"]')
      .should('be.visible')
    
    // Check that table has expected columns
    cy.get('[data-testid="queue-table-headers"]')
      .should('contain.text', 'Status')
      .and('contain.text', 'Role')
      .and('contain.text', 'Model')
  })

  it('maintains WebSocket connection and shows real-time updates', () => {
    // Check that WebSocket connection indicator is present
    cy.get('[data-testid="websocket-status"]')
      .should('be.visible')
      .and('contain.text', 'Connected')
    
    // Submit a query and check for real-time updates
    cy.get('[data-testid="query-tab"]').click()
    cy.get('[data-testid="query-input"]')
      .type('Бюджет GESN 8-6-1.1 Москва')
    cy.get('[data-testid="submit-query"]').click()
    
    // Check for progress updates via WebSocket
    cy.get('[data-testid="progress-updates"]', { timeout: 30000 })
      .should('be.visible')
  })
})