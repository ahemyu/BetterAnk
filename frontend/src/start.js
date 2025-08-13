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

    }catch (error){
        console.error("Error fetching user: ", error);
        localStorage.removeItem("authToken");
        window.location.href = "login.html";
    }

        // Now we want to display the decks of the current user in a list format
        // for that we need to do a get on /decks
    try {
        const decksResponse = await fetch(
            "/decks", {
                method: "GET",
                headers : {
                    "Authorization": `Bearer ${authToken}`
                }
            });
        if(!decksResponse.ok){
            console.error("Error while fetching decks", error);
        }
        const decks = await decksResponse.json();
        console.log(decks); //TODO REMOVE ME 

        // now display the decks in a list, for that we need to append <li> elements to the container
        const deckDiv = document.getElementById("decks-container");
        const deckUl = deckDiv.querySelector("#decks-list");
        const fragment = document.createDocumentFragment();

        decks.forEach(deck => {
            const li = document.createElement("li");
            li.textContent = deck.name;
            fragment.appendChild(li);
        });

        deckUl.appendChild(fragment);
    }catch (error){
        console.log("Error while displaying Decks", error)
    }

    document.getElementById("logout-link").addEventListener("click", () => {
        localStorage.removeItem("authToken");
    });
});
