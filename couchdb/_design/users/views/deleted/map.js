function(doc)
{
    if(doc.doc_type == "User")
    {
        if(doc.deleted == true)
        {
            emit(null, null);
        }
    }
}
