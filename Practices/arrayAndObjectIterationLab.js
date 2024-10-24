var dairy = ['cheese', 'sour cream', 'milk', 'yogurt', 'ice cream', 'milkshake']

function logDairy() {
    for (const iterator of dairy) {
        console.log(iterator);
    }

}

logDairy();


let animal = {

canJump: true
    
};
    
let bird = Object.create(animal);
    
bird.canFly = true;
    
bird.hasFeathers = true;


function birdCan() {
    for (const key of Object.keys(bird)) {
        console.log(`${key}: ${bird[key]}` + "XX");
    }
}

birdCan();

function animalCan() {
    for (const key in bird) {
        console.log(`${key}: ${bird[key]}`);
    }
}

animalCan();

dairy.forEach((element, index) => {
    console.log(`${index}. ${element}`);
});