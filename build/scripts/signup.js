const idNumberInput = document.querySelector("#form-idNumber-input");
const passwordInput = document.querySelector("#form-password-input");
const fullLegalNameInput = document.querySelector("#form-fullName-input");
const forgotPasswordText = document.querySelector("#forgotPassword");
const createAccountButton = document.querySelector("#createAccount-button");
const loginRedirectText = document.querySelector("#subtext-login-redirect");


loginRedirectText.addEventListener("click", (_) => {
  window.open('./login', "_self");
})


createAccountButton.addEventListener("click", (_) => {
  if ((!idNumberInput.value) || (!passwordInput.value) || (!fullLegalNameInput.value)) return;
  fetch(
    `http://127.0.0.1:8000/api/v1/users/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        "_id": idNumberInput.value,
        "full_name": fullLegalNameInput.value,
        "password": passwordInput.value
      })
    }
  ).then(
    response => response.json()
  ).then(
    _ => window.open('./login', "_self")
  )
})