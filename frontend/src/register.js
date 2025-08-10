
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("register-form");

    form.addEventListener("submit", async (event) => {
        event.preventDefault(); //stop the page from reloading

        const email = document.getElementById("register-email").value
        const username = document.getElementById("register-username").value;
        const password = document.getElementById("register-password").value;
        
        const body = {
            "email": email,
            "username": username,
            "password": password,
        } 
        try {
            // now we need to send username and password to /login endpoint from our backend to get the auth_token back and store it in local storage
            const registerResponse = await fetch("/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(body)
            });

            if(!registerResponse.ok){
                console.error("Registration failed!");
                return;
            }

            const loginBody = new URLSearchParams();
            loginBody.append("username", username);
            loginBody.append("password", password);

            const loginResponse = await fetch("/login",{
                method: "POST",
                headers: {
                "Content-Type": "application/x-www-form-urlencoded"
                },
                body: loginBody 
            });

            if(!loginResponse.ok){
                console.error("Login Failed, please try again");
                window.location.href = "login.html";
                return;
            }

            const loginData = await loginResponse.json();
            localStorage.setItem("authToken", loginData.access_token);
            window.location.href = "start.html";


        }catch(error){
            console.log(error); //TODO: do smth more useful 
        }
    });
});