
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

var last_combinators = undefined;

var clstate = {
    "selected_deck": null,
    "binding_fv": -1, // -1 = not binding, n = binding, selected variant n
    "fv_name": "",
};

var data;

async function read_state() {
    await join_if_needed();

    let resp = await fetch('/api/state', {
        method: 'GET',
        credentials: 'same-origin',
    });
    data = await resp.json();
}

async function render(last_data) {
    players = document.getElementById("players");
    if (!(clstate.binding_fv !== -1 && data.you_are == 0) || last_data === undefined) {
        let left = render_player(data.game.players[0], true, data.you_are == 0);

        players.removeChild(players.children[0]);
        players.insertBefore(left, players.children[0]);
    }
    if (!(clstate.binding_fv !== -1 && data.you_are == 1) || last_data === undefined) {
        let right = render_player(data.game.players[1], false, data.you_are == 1);

        players.removeChild(players.children[1]);
        players.children[0].insertAdjacentElement('afterend', right);
    }

    if (JSON.stringify(data.game.combinators) !== JSON.stringify(last_combinators)) {
        let combinators = render_combinators(data.game.combinators)
        document.getElementById("combinators").innerHTML = "";
        combinators.forEach(e => document.getElementById("combinators").appendChild(e));

        last_combinators = data.game.combinators;
    }
}

async function render_loop() {
    while (true) {
        let last_data = data;
        await read_state();
        await render(last_data);
        await new Promise(r => setTimeout(r, 250));
    }
}

render_loop();


async function action_purchase_combinator(c_idx) {
    await fetch('/api/action/purchase_combinator', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify( { "combinator_idx": c_idx } )
    });

    await read_state();
    await render();
}

async function action_purchase_fv(fv_name) {
    await fetch('/api/action/purchase_free_variable', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify( { "var_name": fv_name } )
    });

    await read_state();
    await render();
}

async function action_apply(caller, callee) {
    await fetch('/api/action/apply', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify( { "caller_idx": caller, "callee_idx": callee, } )
    });

    await read_state();
    await render();
}

async function action_eval(idx) {
    await fetch('/api/action/eval', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify( { "deck_idx": idx } )
    });

    await read_state();
    await render();
}

async function action_bind(idx, name) {
    await fetch('/api/action/bind_variable', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify( { "bind_name": name, "deck_idx": idx, } )
    });

    await read_state();
    await render();
}

document.getElementById("new-game").onclick = (e) => {
    document.cookie = "sec_token=";
}
