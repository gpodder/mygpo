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

    function checkChange(newDoc, oldDoc, field)
    {
        message = field + " must not change";
        if(newDoc && oldDoc && oldDoc[field] && (newDoc[field] != oldDoc[field]))
        {
            throw({forbidden: message});
        }
    }

    function check(cond, message)
    {
        message = message || "Condition check failed";
        if(!cond)
        {
            throw({forbidden: message});
        }
    }

    if(newDoc.doc_type == "PodcastGroup")
    {
        for(i in newDoc.podcasts)
        {
            require(newDoc.podcasts[i], "id");
            require(newDoc.podcasts[i], "group");
            check(newDoc.podcasts[i].group == newDoc._id);
            checkChange(newDoc.podcasts[i], oldDoc.podcasts[i], "id");
        }
    }
}
