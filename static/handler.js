
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
    "selected_deck": -1,
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

async function render() {
    let left = render_player(data.game.players[0], true, data.you_are == 0);
    let right = render_player(data.game.players[1], false, data.you_are == 1);

    document.getElementById("players").innerHTML = "";
    document.getElementById("players").appendChild(left);
    document.getElementById("players").appendChild(right);

    if (JSON.stringify(data.game.combinators) !== JSON.stringify(last_combinators)) {
        let combinators = render_combinators(data.game.combinators)
        document.getElementById("combinators").innerHTML = "";
        combinators.forEach(e => document.getElementById("combinators").appendChild(e));

        last_combinators = data.game.combinators;
    }
}

async function render_loop() {
    while (true) {
        await read_state();
        await render();
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
