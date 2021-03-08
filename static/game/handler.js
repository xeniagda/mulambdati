const game_id = new URLSearchParams(window.location.search).get('game_id');

if (game_id === null) {
    window.location.href = "/lobby.html";
}

function mkrq(path) {
    const searchParams = new URLSearchParams({"game_id": game_id});
    return path + "?" + searchParams.toString();
}


async function join_if_needed() {
    let state = await fetch(mkrq('api/state'), {
        method: 'POST',
    });

    if (state.status == 400) {
        await do_req('api/join_game');
    }
}

var last_combinators = undefined;

var clstate = {
    "selected_deck": null,
    "binding_fv": -1, // -1 = not binding, n = binding, selected variant n
    "fv_name": "",
};

async function do_req(url, data) {
    data['sec_token'] = localStorage.getItem("sec_token");
    json_res = await (await fetch(mkrq(url), {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify( data )
    })).json();

    if (json_res["new_sec_token"] !== undefined) {
        localStorage.setItem("sec_token", json_res["new_sec_token"]);
    }

    return json_res;
}

var data;

async function read_state() {
    await join_if_needed();

    data = await do_req('api/state', {});
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
    await do_req('api/action/purchase_combinator', { "combinator_idx": c_idx });

    await read_state();
    await render();
}

async function action_purchase_fv(fv_name) {
    await do_req('api/action/purchase_free_variable', { "var_name": fv_name });

    await read_state();
    await render();
}

async function action_apply(caller, callee) {
    await do_req('api/action/apply', { "caller_idx": caller, "callee_idx": callee, });

    await read_state();
    await render();
}

async function action_eval(idx) {
    await do_req('api/action/eval', { "deck_idx": idx });

    await read_state();
    await render();
}

async function action_bind(idx, name) {
    await do_req('api/action/bind_variable', { "bind_name": name, "deck_idx": idx, });

    await read_state();
    await render();
}

