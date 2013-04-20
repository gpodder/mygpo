function(doc, req)
{
    if(doc._deleted)
    {
        return false;
    }

    return (doc.doc_type && doc.doc_type == req.query.doc_type);
}
