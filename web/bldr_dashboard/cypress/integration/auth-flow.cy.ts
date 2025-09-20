describe('Authentication Flow', () => {
  it('should allow user to login and logout', () => {
    cy.visit('/');
    
    // Check that login button is visible
    cy.get('[data-cy=login-btn]').should('be.visible');
    
    // Click login button
    cy.get('[data-cy=login-btn]').click();
    
    // Check that login modal is visible
    cy.get('.ant-modal-title').should('contain', 'Вход в систему');
    
    // Fill in login form
    cy.get('[data-cy=username]').type('admin');
    cy.get('[data-cy=password]').type('password');
    
    // Submit login form
    cy.get('[data-cy=submit-login]').click();
    
    // Check that user is logged in
    cy.get('.ant-avatar').should('be.visible');
    cy.get('button').contains('Выход').should('be.visible');
    
    // Click logout
    cy.get('.ant-avatar').click();
    cy.get('button').contains('Выход').click();
    
    // Check that user is logged out
    cy.get('[data-cy=login-btn]').should('be.visible');
  });
});

describe('Project Management', () => {
  it('should allow user to create a project', () => {
    cy.visit('/');
    
    // Navigate to projects page
    cy.contains('Проекты').click();
    
    // Click new project button
    cy.get('[data-cy=new-project]').click();
    
    // Fill in project form
    cy.get('[data-cy=project-name]').type('Test Project');
    cy.get('[data-cy=submit-create]').click();
    
    // Check that project is created
    cy.get('[data-cy=projects-table]').contains('Test Project');
  });
});

describe('Settings Management', () => {
  it('should allow user to change settings', () => {
    cy.visit('/');
    
    // Navigate to settings page
    cy.contains('Настройки').click();
    
    // Change RAG k value
    cy.get('[data-cy=rag-k]').invoke('val', 20).trigger('change');
    
    // Save settings
    cy.get('[data-cy=save-settings]').click();
    
    // Check that settings are saved
    cy.get('.ant-message').contains('Настройки сохранены!');
  });
});