function element_with_class_and_text(tag, className, content) {
    var element = document.createElement(tag);
    element.className = className;
    element.innerText = content;
    return element;
}

function render_lambda_expression(lambda_expr) {
    return element_with_class_and_text("span", "", "λa .`c  (???) what");
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
        let rendered = render_lambda_expression();
        let card = element_with_class_and_text("div", "card", "");

        card.appendChild(rendered);
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
        var cost = element_with_class_and_text("div", "comb-number", combinatorData.price + "𐌼");
        heading.appendChild(cost);

        combinator.appendChild(heading);

        var description = element_with_class_and_text("div", "comb-description", combinatorData.name);
        combinator.appendChild(description);

        combinators.push(combinator);

    });

    return combinators;
}
