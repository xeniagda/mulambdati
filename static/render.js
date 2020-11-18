function element_with_class_and_text(tag, className, content) {
    var element = document.createElement(tag);
    element.className = className;
    element.innerText = content;
    return element;
}

function render_player(playerdata, left, is_you) {
    function punctuate(word, punct) {
        return left ? word + punct : punct + word;
    }

    var player = document.createElement("div");
    player.className = "player";

    player.id = left ? "player-1" : "player-2";

    if (is_you) {
        player.className += " you";
    }

    var stats = element_with_class_and_text("div", "stats", "");
    stats.appendChild(element_with_class_and_text("h3", "plname", "Player " + (1 + left)));
    stats.appendChild(document.createTextNode("Health: " + playerdata.health));
    stats.appendChild(element_with_class_and_text("br", "", ""));
    stats.appendChild(document.createTextNode("Mana: " + playerdata.mana + "𐌼"));

    player.appendChild(stats);
    player.appendChild(element_with_class_and_text("h3", "", punctuate("Deck", ":", "")));

    var deck = element_with_class_and_text("div", "deck", "");
    for (var i = 0; i < playerdata.deck.length; i++) {
        let term = playerdata.deck[i];

        let card = element_with_class_and_text("div", "card", "");
        let rendered = element_with_class_and_text("div", "term", term.rendered);
        if (clstate.selected_deck == term.id) {
            card.classList.add("card-selected");

            card.onmousedown = async (e) => {
                if (e.target === this) {
                    clstate.selected_deck = null;
                    clstate.binding_fv = -1;
                    await render();
                }
            };

            card.appendChild(rendered);

            var button_container = element_with_class_and_text("div", "button-container", "");;

            if (clstate.binding_fv !== -1) {
                var fv_select = element_with_class_and_text("select", "", "");
                fv_select.id = "fv-select";

                for (var j = 0; j < term.free_vars.length; j++) {
                    let free = term.free_vars[j];
                    var opt = element_with_class_and_text("option", "", free);
                    opt.value = free;
                    if (j === clstate.binding_fv) {
                        opt.selected = true;
                    }
                    fv_select.appendChild(opt);
                }
                var opt_custom = element_with_class_and_text("option", "", "new");
                opt_custom.value = "new-var";
                fv_select.appendChild(opt_custom);

                if (clstate.binding_fv == term.free_vars.length) {
                    opt_custom.selected = true;
                }

                fv_select.onchange = async (e) => {
                    console.log(e.target.selectedIndex);
                    clstate.binding_fv = e.target.selectedIndex;
                    await render();
                };

                button_container.appendChild(fv_select);

                if (clstate.binding_fv == term.free_vars.length) {
                    var varname = element_with_class_and_text("input", "fv-input", "");
                    varname.value = clstate.fv_name;
                    varname.focus();
                    if (clstate.fv_name === "") {
                        varname.classList.add("flash-red");
                    }
                    varname.id = "bind-fv-name";
                    varname.type = "text";
                    varname.placeholder = "x";

                    varname.oninput = async (e) => {
                        clstate.fv_name = e.target.value;

                        if (clstate.fv_name === "") {
                            e.target.classList.add("flash-red");
                        } else {
                            e.target.classList.remove("flash-red");
                        }
                    };

                    button_container.appendChild(varname);
                }

                var perform_button = element_with_class_and_text("div", "button", "perform bind");
                perform_button.onmousedown = ((i) => async (e) => {
                    var bind_name;
                    if (clstate.binding_fv == term.free_vars.length) {
                        bind_name = clstate.fv_name;
                        if (bind_name === "") {
                            return;
                        }
                    } else {
                        bind_name = document.getElementById("fv-select").value;
                    }
                    clstate.selected_deck = null;
                    clstate.binding_fv = -1;

                    await action_bind(i, bind_name);
                    await render();
                })(i);

                button_container.appendChild(perform_button);
            } else {
                var eval_button = element_with_class_and_text("div", "button", "eval");
                eval_button.onmousedown = ((i) => async (e) => {
                    action_eval(i);
                })(i);
                button_container.appendChild(eval_button);

                var bind_fv_button = element_with_class_and_text("div", "button", "bind fv");

                bind_fv_button.onmousedown = async (e) => {
                    clstate.selected_deck = term.id;
                    clstate.binding_fv = 0;
                    await render();
                };

                button_container.appendChild(bind_fv_button);
            }

            card.appendChild(button_container)
        } else {
            card.onmousedown = ((i, term) => async (e) => {
                if (clstate.selected_deck == null) {
                    clstate.selected_deck = term.id;
                } else {
                    var caller = null;
                    for (var j = 0; j < playerdata.deck.length; j++) {
                        if (playerdata.deck[j].id == clstate.selected_deck) {
                            caller = j;
                        }
                    }
                    console.log(caller);
                    clstate.selected_deck = null;
                    await render();
                    if (caller !== null) {
                        await action_apply(caller, i);
                    }
                }
                await render();
            })(i, term);
        card.appendChild(rendered);
        }

        deck.appendChild(card);
    }

    player.appendChild(deck);

    player.onclick = ((player) => async (e) => {
        if (e.target === player || e.target == stats || e.target == deck) {

            clstate.selected_deck = null;
            clstate.binding_fv = -1;

            await render();
        }
    })(player);

    return player;
}

function render_combinators(combinatorsdata) {
    var combinators = [];

    var free_variable = element_with_class_and_text("div", "combinator", "");
    free_variable.id = "free-variable";
    var fv_heading = element_with_class_and_text("div", "comb-heading", "");
    var fv_number = element_with_class_and_text("div", "comb-number", "-1");
    fv_heading.appendChild(fv_number);
    var fv_cost = element_with_class_and_text("div", "comb-number", "2𐌼");
    fv_heading.appendChild(fv_cost);

    free_variable.appendChild(fv_heading);

    var description = element_with_class_and_text("div", "comb-description", "");
    description.appendChild(document.createTextNode("Free Variable"));
    description.appendChild(element_with_class_and_text("br", "", ""));
    description.appendChild(document.createTextNode("(might cost money)"));
    description.appendChild(element_with_class_and_text("br", "", ""));
    var input = element_with_class_and_text("input", "fv-input", clstate.fv_name);

    input.oninput = (e) => {
        clstate.fv_name = e.target.value;
    };

    free_variable.onmousedown = async (e) => {
        if (e.target == input) {
            return;
        }
        if (clstate.fv_name == "") {
            input.classList.add("flash-red");
        } else {
            free_variable.classList.add("clicked");
            await action_purchase_fv(clstate.fv_name);
        }
    };

    free_variable.onmouseup = (e) => {
        free_variable.classList.remove("clicked")
        input.classList.remove("flash-red");
    };

    input.id = "fv-name";
    input.type = "text";
    input.placeholder = "x";
    description.appendChild(input);

    free_variable.appendChild(description);

    combinators.push(free_variable);

    combinatorsdata.forEach((combinatorData, i) => {
        var combinator = element_with_class_and_text("div", "combinator", "");
        var heading = element_with_class_and_text("div", "comb-heading", "");
        var number = element_with_class_and_text("div", "comb-number", i);
        heading.appendChild(number);

        combinator.onclick = ((i) => async (e) => {
            await action_purchase_combinator(i);
        })(i);

        var cost = element_with_class_and_text("div", "comb-number", combinatorData.price + "𐌼");
        heading.appendChild(cost);

        combinator.appendChild(heading);

        var description = element_with_class_and_text("div", "comb-description", combinatorData.name);
        combinator.appendChild(description);

        combinators.push(combinator);

    });

    return combinators;
}
