function element_with_class_and_text(tag, className, content) {
    var element = document.createElement(tag);
    element.className = className;
    element.innerText = content;
    return element;
}

