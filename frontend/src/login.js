
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("login-form");

    form.addEventListener("submit", async (event) => {
        event.preventDefault(); //stop the page from reloading

        const username = document.getElementById("username");
        const password = document.getElementById("password");

        const body = new URLSearchParams();

        body.append("username", username);
        body.append("password", password);

        try {
            // now we need to send username and password to /login endpoint from our backend to get the auth_token back and store it in local storage
            const response = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: body.toString()
            });

            const data = await response.json(); //data is now the auth token

            localStorage.setItem('authToken', data.access_token);

        }catch(error){
            console.log(error); //TODO: do smth more useful 
        }
    });
});