/// <reference types="cypress" />

describe('Bldr Empire v2 - Telegram Bot E2E Tests', () => {
  beforeEach(() => {
    // Visit the application
    cy.visit('http://localhost:3000')
    
    // Wait for the app to load
    cy.get('[data-testid="app-loaded"]', { timeout: 10000 }).should('be.visible')
  })

  it('simulates TG bot interaction and shows results', () => {
    // Navigate to TG bot simulation tab
    cy.get('[data-testid="tg-bot-tab"]').click()
    
    // Enter TG bot query text
    cy.get('[data-testid="tg-query-input"]')
      .type('Анализ фото site.jpg на SanPiN + timeline проект LSR')
    
    // Upload a sample photo for TG bot
    cy.get('[data-testid="tg-file-upload"]').selectFile({
      contents: Cypress.Buffer.from('mock image content'),
      fileName: 'site.jpg',
      mimeType: 'image/jpeg'
    })
    
    // Submit the TG bot query
    cy.get('[data-testid="tg-submit-query"]').click()
    
    // Check that initial response is shown
    cy.get('[data-testid="tg-initial-response"]', { timeout: 30000 })
      .should('be.visible')
      .and('contain.text', 'План: complexity med')
    
    // Check that progress steps are displayed
    cy.get('[data-testid="tg-progress-steps"]', { timeout: 30000 })
      .should('be.visible')
      .find('[data-testid="progress-step"]')
      .should('have.length.at.least', 4)
    
    // Wait for parse step to complete
    cy.get('[data-testid="parse-step"]', { timeout: 60000 })
      .should('have.class', 'completed')
    
    // Wait for plan step to complete
    cy.get('[data-testid="plan-step"]', { timeout: 60000 })
      .should('have.class', 'completed')
    
    // Check that final response with ZIP attachment is shown
    cy.get('[data-testid="tg-final-response"]', { timeout: 120000 })
      .should('be.visible')
      .and('contain.text', 'analysis.docx')
      .and('contain.text', 'timeline.gantt')
    
    // Check that download buttons for attachments are available
    cy.get('[data-testid="tg-download-analysis"]')
      .should('be.visible')
      .and('be.enabled')
    
    cy.get('[data-testid="tg-download-timeline"]')
      .should('be.visible')
      .and('be.enabled')
  })

  it('handles TG bot errors gracefully', () => {
    // Navigate to TG bot simulation tab
    cy.get('[data-testid="tg-bot-tab"]').click()
    
    // Enter TG bot query text
    cy.get('[data-testid="tg-query-input"]')
      .type('Invalid query with missing data')
    
    // Submit the TG bot query without file
    cy.get('[data-testid="tg-submit-query"]').click()
    
    // Check for error message
    cy.get('[data-testid="tg-error-toast"]', { timeout: 10000 })
      .should('be.visible')
      .and('contain.text', 'Error')
  })
})