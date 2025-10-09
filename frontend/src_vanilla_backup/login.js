
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("login-form");

    form.addEventListener("submit", async (event) => {
        event.preventDefault(); //stop the page from reloading

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        const body = new URLSearchParams();

        body.append("username", username);
        body.append("password", password);

       console.log("Submitting login form...");

    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: body.toString()
        });

        if (!response.ok) {
            console.error("Login failed");
            return;
        }

        const data = await response.json();

        localStorage.setItem('authToken', data.access_token);

        window.location.href = "start.html";

    }catch (error) {
        console.error("Error during login:", error);
    }
        });
});