// language choice - NOT USED FOR NOW
document.addEventListener("DOMContentLoaded", function () {

    const languageFilter = document.getElementById("language");

    if (!languageFilter) return;

    const updateURL = () => {

        const newURL = new URL(window.location.href);
        const languageValue = languageFilter.value;

        if (languageValue) {
            newURL.searchParams.set("language", languageValue);
        } else {
            newURL.searchParams.delete("language");
        }

        window.location.href = newURL.toString();
    };

    languageFilter.addEventListener("change", updateURL);
});    


// global empty array for the checkBox state change
let CheckBoxAlarm = [];

function CheckBoxClick(checkbox){

    // checkbox.value == alarm.titolo
    const title = checkbox.value; 

    // print alarm.titolo correctly
    console.log(checkbox.value);

    if(checkbox.checked){

        // add to the list 
        CheckBoxAlarm.push(title);
    }else{

        // remove from the list
        const index = CheckBoxAlarm.indexOf(title);
        if(index > -1){
            CheckBoxAlarm.splice(index, 1);
        }
    }
    //console.log(CheckBoxAlarm.length)
    console.log(CheckBoxAlarm)
}


function SendCheckBoxList(dowload){
    console.log(download);
    console.log(CheckBoxAlarm);
    console.log("Valore input:", document.getElementById("form-lista").value);
    document.getElementById("CheckBoxList").value = JSON.stringify(CheckBoxAlarm);
    document.getElementById("form-lista").submit();
}


// ModifyText

