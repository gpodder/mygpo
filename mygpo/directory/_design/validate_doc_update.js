function(newDoc, oldDoc, userCtx)
{
    String.prototype.trim = function()
    {
        return this.replace(/^\s+|\s+$/g,"");
    }

    function require(field, message)
    {
        message = message || "Document must have a " + field;
        if (newDoc[field] == void 0 || newDoc[field] == null)
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

    function checkTrimmed(field)
    {
        if (newDoc[field] != newDoc[field].trim())
        {
            throw({forbidden: field + " must be trimmed"});
        }
    }

    function checkUnique(arr, field)
    {
        for(n in arr)
        {
            function f(x) {return x==arr[n];};
            if(arr.filter(f).length > 1)
            {
                throw({forbidden: field + " must be unique"});
            }
        }
    }


    if(newDoc.doc_type == "Category")
    {
        require("label");
        check(newDoc.label != "", "label must not be empty");
        checkTrimmed("label");

        require("weight");
        check(newDoc.weight >= 0, "weight must not be negative");

        require("updated");

        if (newDoc.spellings)
        {
            check(newDoc.spellings.indexOf(newDoc.label) < 0,
                    "The label should not be contained in the alternative spellings");
            checkUnique(newDoc.spellings, "spellings");
        }
    }
}

