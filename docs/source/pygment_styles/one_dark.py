"""Custom pygment style."""
from pygments.style import Style
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Name,
    Number,
    Operator,
    String,
    Text,
)


class OneDark(Style):  # type: ignore
    """A clone of the One Dark theme."""

    default_style = ""
    styles = {
        Comment: "italic #5B6370",
        Comment.Multiline: "italic #5B6370",
        Comment.Preproc: "bold #5B6370",
        Comment.Single: "italic #5B6370",
        Comment.Special: "bold italic #5B6370",
        Error: "bg:#1e0010 #960050",
        Generic.Deleted: "bg:#fdd #000",
        Generic.Deleted.Specific: "bg:#faa #000",
        Generic.Emph: "italic",  # cspell:ignore emph
        Generic.Error: "#a00",
        Generic.Heading: "#5B6370",
        Generic.Inserted: "bg:#dfd #a6e22e",
        Generic.Inserted.Specific: "bg:#afa #a6e22e",
        Generic.Output: "#888",
        Generic.Prompt: "#555",
        Generic.Strong: "bold",
        Generic.Subheading: "#aaa ",
        Generic.Traceback: "#a00 ",
        Keyword: "bold #C776DF",
        Keyword.Constant: "bold",
        Keyword.Constant.Escape: "#65ADB2",
        Keyword.Declaration: "bold #C776DF",
        Keyword.Pseudo: "bold",
        Keyword.Reserved: "bold",
        Keyword.Type: "bold #458",
        Name.Attribute: "#E2964A",
        Name.Builtin: "#4FB6C3",
        Name.Builtin.Pseudo: "#EBBF6F",
        Name.Class: "bold #EBBF6F",
        Name.Decorator: "#4FB6BE",
        Name.Constant: "#4FB6BE",
        Name.Entity: "#E2964A",
        Name.Exception: "bold #900",
        Name.Function: "bold #52A5EB",
        Name.Tag: "#DE5442",
        Name.Variable: "#DE5442",
        Name.Variable.Class: "#008080",
        Name.Variable.Global: "#008080",
        Name.Variable.Instance: "#008080",
        Number: "#4FB6C3",
        Number.Float: "#4FB6C3",
        Number.Hex: "#4FB6C3",
        Number.Integer: "#4FB6C3",
        Number.Integer.Long: "#4FB6C3",
        Number.Oct: "#4FB6C3",
        Operator: "bold",
        Operator.Word: "bold",
        String: "#A2BD40",
        String.Backtick: "#A2BD40",
        String.Char: "#A2BD40",
        String.Documentation: "#A2BD40",
        String.Double: "#A2BD40",
        String.Escape: "#65ADB2",
        String.Heredoc: "#A2BD40",
        String.Interpol: "#A2BD40",
        String.Other: "#A2BD40",
        String.Regex: "#009926 ",
        String.Single: "#A2BD40",
        String.Symbol: "#990073",
        Text.Whitespace: "#bbb",
    }
