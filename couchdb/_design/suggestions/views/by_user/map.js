function(doc)
{
    if(doc.doc_type == "Suggestions")
    {
        emit(doc.user, null);
    }
}
