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
                clstate.selected_deck = null;
                await render();
            };

            card.appendChild(rendered);

            var eval_button = element_with_class_and_text("div", "button", "eval");
            eval_button.onmousedown = ((i) => async (e) => {
                action_eval(i);
            })(i);

            card.appendChild(eval_button);
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
    var input = element_with_class_and_text("input", "", clstate.fv_name);

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
