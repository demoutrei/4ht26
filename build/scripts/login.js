const idNumberInput = document.querySelector("#form-idNumber-input");
const passwordInput = document.querySelector("#form-password-input");
const loginButton = document.querySelector("#login-button");
const createAccountRedirectText = document.querySelector("#subtext-createAccount-redirect");


createAccountRedirectText.addEventListener("click", (_) => {
  window.open('./signup', "_self");
})


loginButton.addEventListener("click", (_) => {
  if (!idNumberInput.value || !passwordInput.value) return;
  fetch(
    `http://127.0.0.1:8000/api/v1/users/${idNumberInput.value}`
  ).then(
    response => response.json()
  ).then(
    data => {
      console.log(data["password"]);
      console.log(passwordInput.value != data["password"]);
      if (passwordInput.value != data["password"]) return;
      window.open(`/u/${idNumberInput.value}/dashboard`, "_self");
    }
  )
})