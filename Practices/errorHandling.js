/*
function addTwoNums(a , b) {
    try {

        if  (typeof a != "number") {
            throw new ReferenceError("the first argument is not a number")
        }
        else if (typeof b != "number" ){
            throw new ReferenceError("the recond argument is not a number")
        }
        else{
            console.log(a+b);
        }
    }
    catch(err){
        console.log("Error!" , err)
    }
    console.log("It still works")

}
addTwoNums(5,"5");
*/

function letterFinder(word, match) {
    for(var i = 0; i < word.length; i++) {

        var condition = typeof(word) == "string" && typeof(match) == "string";
        var condition2 = word.length > 2 && match.length == 1

        if (condition && condition2) {
            if(word[i] == match) {
                //if the current character at position i in the word is equal to the match
                console.log('Found the', match, 'at', i)
            } else {
                console.log('---No match found at', i)
            }
        }
        else {
            console.log("Please pass correct arguments to the function.")
            return
        }

        
    }
}
letterFinder([],[])
letterFinder("cat","c")

