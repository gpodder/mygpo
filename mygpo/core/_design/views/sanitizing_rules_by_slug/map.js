function(doc)
{
    if(doc.doc_type == "SanitizingRule")
    {
        emit(doc.slug, null);
    }
}
