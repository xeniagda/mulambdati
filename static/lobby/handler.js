var created_games = new Set();

async function load_and_render_games() {
    let games = await fetch('/api/get_games');
    let data = await games.json();

    var lobby = document.getElementById("lobby");
    lobby.innerHTML = "";
    console.log(data);

    for (var i = 0; i < data.games.length; i++) {
        lobby.appendChild(await render_game(i, data.games[i]));
    }
}

document.getElementById("create-new-game").onclick = async e => {
    let created = await fetch('/api/create_new_game', { "method": "POST" });
    let data = await created.json();
    created_games.add(data["created_id"]);

    await load_and_render_games();
};

load_and_render_games();

async function render_game(i, gamedata) {
    console.log(gamedata);
    var game = element_with_class_and_text("div", "game", "");
    game.appendChild(element_with_class_and_text("h3", "", "Game #" + i));
    game.appendChild(element_with_class_and_text("br", "", ""));
    game.appendChild(element_with_class_and_text("span", "name", gamedata.game_identifier));
    game.appendChild(element_with_class_and_text("br", "", ""));

    var all_joined = true;
    var members = [];
    for (var i = 0; i < gamedata.players.length; i++) {
        let player = gamedata.players[i];
        if (player.has_been_claimed) {
            members.push(player.user_name);
        } else {
            all_joined = false;
        }
    }

    game.appendChild(element_with_class_and_text(
        "span",
        "n_players",
        "(" + members.length + "/" + gamedata.players.length + ")"
    ));

    game.appendChild(document.createTextNode(", "));
    if (!all_joined) {
        if (members.length > 0) {
            for (var i = 0; i < members.length; i++) {
                if (i > 0) {
                    game.appendChild(document.createTextNode(i == members.length - 1 ? " and " : ", "));
                }
                game.appendChild(element_with_class_and_text(
                    "span",
                    "user",
                    members[i],
                ));
            }
            game.appendChild(document.createTextNode(members.length == 1 ? " is " : " are "));
            game.appendChild(document.createTextNode("waiting."));
        }
    } else {
        game.appendChild(document.createTextNode("this game is "));
        game.appendChild(element_with_class_and_text("span", "user", "full"));
        game.appendChild(document.createTextNode(" but you can still "));
        game.appendChild(element_with_class_and_text("span", "user", "spectate"));
        game.appendChild(document.createTextNode("!"));
        game.classList.add("full");
    }

    if (created_games.has(gamedata.game_identifier)) {
        game.classList.add("your");
    }

    game.appendChild(element_with_class_and_text("br", "", ""));
    var enter_link = element_with_class_and_text("a", "", "Enter!");

    let searchParams = new URLSearchParams({"game_id": gamedata.game_identifier});
    enter_link.href = "game.html?" + searchParams.toString();
    game.appendChild(enter_link);

    return game;
}
