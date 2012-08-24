function(newDoc, oldDoc, userCtx)
{
    function require(doc, field, message)
    {
        message = message || "Document must have a " + field;
        if (doc[field] == void 0 || doc[field] == null || doc[field].length == 0)
        {
            throw({forbidden: message});
        }
    }

    if(newDoc.doc_type == "Episode")
    {
        require(newDoc, "urls");
        require(newDoc, "podcast");
    }
}
