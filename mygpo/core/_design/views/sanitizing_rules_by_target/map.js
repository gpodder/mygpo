function(doc)
{
    if(doc.doc_type == "SanitizingRule")
    {
        for(n in doc.applies_to)
        {
            emit([doc.applies_to[n], doc.priority], null);
        }
    }
}
