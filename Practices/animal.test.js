const { Animal, Cat, Bird, HouseCat, Tiger, Parrot } = require('./designingOOProgram');

describe('Animal Classes', () => {
    test('Polly should make a chirp sound and then talk', () => {
        const polly = new Parrot(true);
        console.log = jest.fn();
        polly.makeSound(true);
        expect(console.log).toHaveBeenCalledWith('chirp');
        expect(console.log).toHaveBeenCalledWith("I'm talking parrot!");
    });

    test('Fiji should only make a chirp sound', () => {
        const fiji = new Parrot(false);
        console.log = jest.fn();
        fiji.makeSound(true);
        expect(console.log).toHaveBeenCalledWith('chirp');
    });

    test('HouseCat should make both sounds when option is true', () => {
        const houseCat = new HouseCat('meow', 'purr');
        console.log = jest.fn();
        houseCat.makeSound(true);
        expect(console.log).toHaveBeenCalledWith('purr');
        expect(console.log).toHaveBeenCalledWith('meow');
    });

    test('HouseCat should make only house cat sound when option is false', () => {
        const houseCat = new HouseCat('meow', 'purr');
        console.log = jest.fn();
        houseCat.makeSound(false);
        expect(console.log).toHaveBeenCalledWith('meow');
    });

    test('Tiger should make both sounds when option is true', () => {
        const tiger = new Tiger('Roar!', 'growl');
        console.log = jest.fn();
        tiger.makeSound(true);
        expect(console.log).toHaveBeenCalledWith('growl');
        expect(console.log).toHaveBeenCalledWith('Roar!');
    });

    test('Tiger should make only tiger sound when option is false', () => {
        const tiger = new Tiger('Roar!', 'growl');
        console.log = jest.fn();
        tiger.makeSound(false);
        expect(console.log).toHaveBeenCalledWith('Roar!');
    });
});
