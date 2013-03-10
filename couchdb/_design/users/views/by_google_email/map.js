function(doc)
{
    if(doc.doc_type == "User")
    {
        if(doc.google_email)
        {
            emit(doc.google_email, null);
        }
    }
}
