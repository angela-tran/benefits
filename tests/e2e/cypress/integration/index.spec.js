describe("Index page spec", () => {
    it("Gives user transit provider options", () => {
        cy.visit("/")

        cy.contains("Choose your transit provider")
          .siblings(".btn")
          .should('not.be.empty')
          .each(($e) => {
              expect($e).attr("href").to.match(/\/[a-z]{3,}$/)
          })
    })

    it("Takes user to transit provider page", () => {
        cy.visit("/")

        cy.get(".buttons .btn")
          .first()
          .click()

        cy.contains("Let’s do it!")
          .then(($e) => {
            expect($e).attr("href").to.match(/\/eligibility\/$/)
          })
    })
})