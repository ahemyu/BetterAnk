
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
            const response = await fetch("/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(body)
            });

            if(response.ok){
                window.location.href = "login.html" //ToDo: call /login immediately for auto login
            }
        }catch(error){
            console.log(error); //TODO: do smth more useful 
        }
    });
});