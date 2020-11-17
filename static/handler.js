
async function join_if_needed() {
    let state = await fetch('/api/state', {
        method: 'GET',
        credentials: 'same-origin',
    });

    if (state.status == 400) {
        await fetch('/api/join_game', {
            method: 'POST',
            credentials: 'same-origin',
        });
    }
}

async function read_state() {
    await join_if_needed();

    let resp = await fetch('/api/state', {
        method: 'GET',
        credentials: 'same-origin',
    });
    let data = await resp.json();
    console.log(data);

    let left = render_player(data.game.players[0], true, data.you_are == 0);
    let right = render_player(data.game.players[1], false, data.you_are == 1);

    document.getElementById("players").innerHTML = "";
    document.getElementById("players").appendChild(left);
    document.getElementById("players").appendChild(right);

    let combinators = render_combinators(data.game.combinators)
    document.getElementById("combinators").innerHTML = "";
    combinators.forEach(e => document.getElementById("combinators").appendChild(e));

    await new Promise(r => setTimeout(r, 250));
    await read_state(); // Hopefully stack doesn't overflow lol
}

read_state();
