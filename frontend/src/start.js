document.addEventListener("DOMContentLoaded", async () => {

    const authToken = localStorage.getItem("authToken");
    if(!authToken){
        // if no auth token redirect to login page
        window.location.href = "login.html";
        return;
    }
    try {
    
        //call /me endpoint to get the current user
        const response = await fetch(
            "/me",{
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${authToken}`
                }
            });
        if(!response.ok){
            // token invalid, delete current one and redirect to login
            localStorage.removeItem("authToken");
            window.location.href = "login.html";
            return;
        }

        const user = await response.json();
        document.getElementById("welcome-message").textContent = `Welcome, ${user.username}!`
        
    
    } catch (error){
        console.error("Error fetching user: ", error);
        localStorage.removeItem("authToken");
        window.location.href = "login.html";
    }

    document.getElementById("logout-link").addEventListener("click", () => {
        localStorage.removeItem("authToken");
    });
});
