function(doc)
{
    if(doc.doc_type == 'User')
    {
        for(id in doc.devices)
        {
            device = doc.devices[id];
            emit([doc.oldid, device.uid], device);
        }
    }
}
