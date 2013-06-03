function(doc)
{
    if(doc.doc_type == "Subscription")
    {
        emit(doc.url, null);
    }
}
