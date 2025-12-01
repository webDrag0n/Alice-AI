const mineflayer = require('mineflayer');
const { pathfinder, Movements, goals } = require('mineflayer-pathfinder');
const collectBlock = require('mineflayer-collectblock').plugin;
const toolPlugin = require('mineflayer-tool').plugin;
const autoEat = require('mineflayer-auto-eat').plugin;
const Vec3 = require('vec3');

class BotManager {
    constructor() {
        this.bot = null;
        this.config = null;
        this.state = {
            status: 'disconnected',
            lastError: null,
            currentAction: null,
            danger: false,
            chatHistory: []
        };
    }

    start(options) {
        if (this.bot) {
            this.stop();
        }

        this.config = options;
        this.bot = mineflayer.createBot(options);

        this.initPlugins();
        this.initEvents();
        this.state.status = 'connecting';
    }

    stop() {
        if (this.bot) {
            this.bot.quit();
            this.bot = null;
            this.state.status = 'disconnected';
        }
    }

    initPlugins() {
        this.bot.loadPlugin(pathfinder);
        this.bot.loadPlugin(collectBlock);
        this.bot.loadPlugin(toolPlugin);
        this.bot.loadPlugin(autoEat);
    }

    initEvents() {
        this.bot.on('spawn', () => {
            this.state.status = 'connected';
            console.log('Bot spawned');
            
            // AuthMe login
            setTimeout(() => {
                this.bot.chat('/login wonderland');
                console.log('Sent /login wonderland for AuthMe authentication');
            }, 2000); // Wait 2 seconds to ensure server is ready

            // Setup pathfinder movements
            const mcData = require('minecraft-data')(this.bot.version);
            const defaultMove = new Movements(this.bot, mcData);
            this.bot.pathfinder.setMovements(defaultMove);

            // Setup auto-eat
            this.bot.autoEat.options = {
                priority: 'foodPoints',
                startAt: 14,
                bannedFood: []
            };

        });

        this.bot.on('error', (err) => {
            console.error('Bot error:', err);
            this.state.lastError = err.message;
        });

        this.bot.on('end', () => {
            this.state.status = 'disconnected';
            console.log('Bot disconnected');
        });

        this.bot.on('health', () => {
            if (this.bot.health < 10) {
                this.state.danger = true;
                console.log('Danger: Low health!');
                this.handleDanger();
            } else {
                this.state.danger = false;
            }
        });

        this.bot.on('entityHurt', (entity) => {
            if (entity === this.bot.entity) {
                this.state.danger = true;
                console.log('Danger: Taking damage!');
                this.handleDanger();
            }
        });

        this.bot.on('food', () => {
            if (this.bot.food < 10) {
                console.log('Hunger: Low food level!');
                this.handleHunger();
            }
        });

        this.bot.on('chat', (username, message) => {
            if (username === this.bot.username) return;
            const chatEntry = { username, message, timestamp: Date.now() };
            this.state.chatHistory.push(chatEntry);
            if (this.state.chatHistory.length > 50) {
                this.state.chatHistory.shift();
            }
            console.log(`Chat: <${username}> ${message}`);
        });
    }

    getStatus() {
        return {
            ...this.state,
            botExists: !!this.bot
        };
    }

    // --- Perception ---

    getPerception() {
        if (!this.bot) return null;
        return {
            position: this.bot.entity.position,
            health: this.bot.health,
            food: this.bot.food,
            saturation: this.bot.foodSaturation,
            oxygen: this.bot.oxygenLevel,
            gameTime: this.bot.time.time,
            day: this.bot.time.day,
            weather: this.bot.rainState,
            danger: this.state.danger,
            chatHistory: this.state.chatHistory.slice(-20),
            inventory: this.getInventory(),
            nearbyEntities: this.getNearbyEntities(10),
            nearbyBlocks: this.getSurroundings()
        };
    }

    getInventory() {
        if (!this.bot) return [];
        return this.bot.inventory.items().map(item => ({
            name: item.name,
            count: item.count,
            type: item.type
        }));
    }

    getNearbyEntities(range) {
        if (!this.bot) return [];
        const entities = [];
        for (const id in this.bot.entities) {
            const entity = this.bot.entities[id];
            if (entity === this.bot.entity) continue;
            if (entity.position.distanceTo(this.bot.entity.position) < range) {
                entities.push({
                    id: entity.id,
                    name: entity.name,
                    type: entity.type,
                    position: entity.position,
                    distance: entity.position.distanceTo(this.bot.entity.position)
                });
            }
        }
        return entities;
    }

    getSurroundings() {
        if (!this.bot) return [];
        // Get blocks in a 5x5x5 area
        const blocks = [];
        const pos = this.bot.entity.position.floored();
        for (let x = -2; x <= 2; x++) {
            for (let y = -1; y <= 3; y++) {
                for (let z = -2; z <= 2; z++) {
                    const block = this.bot.blockAt(pos.offset(x, y, z));
                    if (block && block.name !== 'air') {
                        blocks.push({
                            name: block.name,
                            position: block.position,
                            distance: block.position.distanceTo(this.bot.entity.position)
                        });
                    }
                }
            }
        }
        return blocks;
    }

    // --- Conditional Reflexes ---

    async handleDanger() {
        if (!this.bot) return;

        // Equip best armor first
        await this.equipBestArmor();

        // Count nearby hostile entities
        const nearbyHostiles = this.getNearbyEntities(10).filter(e => this.isHostile(e.name));
        const hostileCount = nearbyHostiles.length;

        if (hostileCount > 3) {
            // Too many enemies, flee
            console.log('Too many enemies, fleeing!');
            await this.flee();
        } else if (hostileCount > 0) {
            // Attack nearest enemy
            console.log('Attacking nearest enemy!');
            await this.equipBestWeapon();
            await this.attackNearestEnemy();
        }
    }

    async handleHunger() {
        if (!this.bot) return;

        // Try to eat food first
        const ate = await this.eatFood();
        if (!ate) {
            // No food, hunt animals
            console.log('No food, hunting animals!');
            await this.huntAnimals();
        }
    }

    async equipBestArmor() {
        if (!this.bot) return;

        const armorSlots = ['head', 'torso', 'legs', 'feet'];
        const armorTypes = ['helmet', 'chestplate', 'leggings', 'boots'];

        for (let i = 0; i < armorSlots.length; i++) {
            const slot = armorSlots[i];
            const type = armorTypes[i];

            // Find best armor of this type
            const bestArmor = this.bot.inventory.items()
                .filter(item => item.name.includes(type))
                .sort((a, b) => this.getArmorProtection(b.name) - this.getArmorProtection(a.name))[0];

            if (bestArmor) {
                try {
                    await this.bot.equip(bestArmor, slot);
                    console.log(`Equipped ${bestArmor.name} in ${slot}`);
                } catch (e) {
                    console.log(`Failed to equip ${bestArmor.name}: ${e.message}`);
                }
            }
        }
    }

    async equipBestWeapon() {
        if (!this.bot) return;

        // Find weapon with highest damage
        const bestWeapon = this.bot.inventory.items()
            .filter(item => this.isWeapon(item.name))
            .sort((a, b) => this.getWeaponDamage(b.name) - this.getWeaponDamage(a.name))[0];

        if (bestWeapon) {
            try {
                await this.bot.equip(bestWeapon, 'hand');
                console.log(`Equipped ${bestWeapon.name} as weapon`);
            } catch (e) {
                console.log(`Failed to equip ${bestWeapon.name}: ${e.message}`);
            }
        }
    }

    async eatFood() {
        if (!this.bot) return false;

        // Find edible food
        const food = this.bot.inventory.items()
            .filter(item => this.isFood(item.name))[0];

        if (food) {
            try {
                await this.bot.equip(food, 'hand');
                await this.bot.consume();
                console.log(`Ate ${food.name}`);
                return true;
            } catch (e) {
                console.log(`Failed to eat ${food.name}: ${e.message}`);
            }
        }
        return false;
    }

    async attackNearestEnemy() {
        if (!this.bot) return;

        const nearbyHostiles = this.getNearbyEntities(10).filter(e => this.isHostile(e.name));
        if (nearbyHostiles.length === 0) return;

        const nearest = nearbyHostiles.sort((a, b) => a.distance - b.distance)[0];
        const entity = this.bot.entities[nearest.id];

        if (entity) {
            try {
                await this.bot.pathfinder.goto(new goals.GoalFollow(entity, 1));
                this.bot.attack(entity);
                console.log(`Attacking ${nearest.name}`);
            } catch (e) {
                console.log(`Failed to attack ${nearest.name}: ${e.message}`);
            }
        }
    }

    async flee() {
        if (!this.bot) return;

        // Find a safe direction (opposite to nearest enemy)
        const nearbyHostiles = this.getNearbyEntities(10).filter(e => this.isHostile(e.name));
        if (nearbyHostiles.length === 0) return;

        const nearest = nearbyHostiles.sort((a, b) => a.distance - b.distance)[0];
        const enemyPos = this.bot.entities[nearest.id]?.position;
        if (!enemyPos) return;

        // Calculate flee direction (opposite to enemy)
        const botPos = this.bot.entity.position;
        const fleeX = botPos.x + (botPos.x - enemyPos.x) * 2;
        const fleeZ = botPos.z + (botPos.z - enemyPos.z) * 2;
        const fleeY = botPos.y;

        try {
            await this.moveTo(fleeX, fleeY, fleeZ);
            console.log('Fled from danger');
        } catch (e) {
            console.log(`Failed to flee: ${e.message}`);
        }
    }

    async huntAnimals() {
        if (!this.bot) return;

        // Find nearest animal
        const nearbyAnimals = this.getNearbyEntities(20).filter(e => this.isAnimal(e.name));
        if (nearbyAnimals.length === 0) {
            console.log('No animals nearby to hunt');
            return;
        }

        const nearest = nearbyAnimals.sort((a, b) => a.distance - b.distance)[0];
        const entity = this.bot.entities[nearest.id];

        if (entity) {
            try {
                await this.equipBestWeapon();
                await this.bot.pathfinder.goto(new goals.GoalFollow(entity, 1));
                this.bot.attack(entity);
                console.log(`Hunting ${nearest.name}`);
            } catch (e) {
                console.log(`Failed to hunt ${nearest.name}: ${e.message}`);
            }
        }
    }

    // Helper methods
    isHostile(name) {
        const hostiles = ['zombie', 'skeleton', 'creeper', 'spider', 'enderman', 'witch', 'blaze', 'ghast'];
        return hostiles.includes(name.toLowerCase());
    }

    isAnimal(name) {
        const animals = ['cow', 'pig', 'sheep', 'chicken', 'rabbit', 'horse', 'donkey', 'llama'];
        return animals.includes(name.toLowerCase());
    }

    isWeapon(name) {
        const weapons = ['sword', 'axe', 'bow', 'crossbow'];
        return weapons.some(w => name.includes(w));
    }

    isFood(name) {
        const foods = ['apple', 'bread', 'cooked_beef', 'cooked_porkchop', 'cooked_chicken', 'cooked_mutton', 'cooked_rabbit', 'carrot', 'potato', 'beetroot'];
        return foods.includes(name);
    }

    getWeaponDamage(name) {
        const damageMap = {
            'wooden_sword': 4,
            'stone_sword': 5,
            'iron_sword': 6,
            'diamond_sword': 7,
            'netherite_sword': 8,
            'wooden_axe': 7,
            'stone_axe': 9,
            'iron_axe': 9,
            'diamond_axe': 9,
            'netherite_axe': 10,
            'bow': 9,
            'crossbow': 9
        };
        return damageMap[name] || 1;
    }

    getArmorProtection(name) {
        const protectionMap = {
            'leather_helmet': 1,
            'leather_chestplate': 3,
            'leather_leggings': 2,
            'leather_boots': 1,
            'chainmail_helmet': 2,
            'chainmail_chestplate': 5,
            'chainmail_leggings': 4,
            'chainmail_boots': 1,
            'iron_helmet': 2,
            'iron_chestplate': 6,
            'iron_leggings': 5,
            'iron_boots': 2,
            'diamond_helmet': 3,
            'diamond_chestplate': 8,
            'diamond_leggings': 6,
            'diamond_boots': 3,
            'netherite_helmet': 3,
            'netherite_chestplate': 8,
            'netherite_leggings': 6,
            'netherite_boots': 3
        };
        return protectionMap[name] || 0;
    }

    // --- Actions ---

    chat(message) {
        if (this.bot) this.bot.chat(message);
    }

    async moveTo(x, y, z) {
        if (!this.bot) throw new Error('Bot not ready');
        const goal = new goals.GoalBlock(x, y, z);
        this.state.currentAction = `Moving to ${x}, ${y}, ${z}`;
        try {
            await this.bot.pathfinder.goto(goal);
        } finally {
            this.state.currentAction = null;
        }
    }

    async mineBlock(x, y, z) {
        if (!this.bot) throw new Error('Bot not ready');
        const block = this.bot.blockAt(new Vec3(x, y, z));
        if (!block) throw new Error('Block not found');
        
        this.state.currentAction = `Mining ${block.name} at ${x}, ${y}, ${z}`;
        try {
            await this.bot.collectBlock.collect(block);
        } finally {
            this.state.currentAction = null;
        }
    }

    async placeBlock(x, y, z, faceVector, itemName) {
        if (!this.bot) throw new Error('Bot not ready');
        const referenceBlock = this.bot.blockAt(new Vec3(x, y, z));
        if (!referenceBlock) throw new Error('Reference block not found');

        const item = this.bot.inventory.items().find(i => i.name === itemName);
        if (!item) throw new Error(`Item ${itemName} not in inventory`);

        this.state.currentAction = `Placing ${itemName} at ${x}, ${y}, ${z}`;
        try {
            await this.bot.equip(item, 'hand');
            await this.bot.placeBlock(referenceBlock, new Vec3(faceVector.x, faceVector.y, faceVector.z));
        } finally {
            this.state.currentAction = null;
        }
    }

    async equipItem(itemName, destination = 'hand') {
        if (!this.bot) throw new Error('Bot not ready');
        const item = this.bot.inventory.items().find(i => i.name === itemName);
        if (!item) throw new Error(`Item ${itemName} not in inventory`);
        
        await this.bot.equip(item, destination);
    }

    async craftItem(itemName, count = 1) {
        if (!this.bot) throw new Error('Bot not ready');
        const mcData = require('minecraft-data')(this.bot.version);
        const item = mcData.itemsByName[itemName];
        if (!item) throw new Error(`Unknown item ${itemName}`);

        const recipe = this.bot.recipesFor(item.id, null, 1, null)[0];
        if (!recipe) throw new Error(`No recipe for ${itemName}`);

        this.state.currentAction = `Crafting ${itemName}`;
        try {
            await this.bot.craft(recipe, count, null);
        } finally {
            this.state.currentAction = null;
        }
    }

    async attackEntity(entityName) {
        if (!this.bot) throw new Error('Bot not ready');
        const entity = this.bot.nearestEntity(e => e.name === entityName);
        if (!entity) throw new Error(`Entity ${entityName} not found`);

        this.state.currentAction = `Attacking ${entityName}`;
        try {
            await this.bot.pvp.attack(entity); // Note: pvp plugin might be needed for complex combat, but basic attack is simple
            // For simple attack without pvp plugin:
            // await this.bot.attack(entity);
            // But pathfinder + attack is better handled by pvp plugin or custom logic.
            // For now, let's just move to and attack once.
            
            const defaultMove = new Movements(this.bot, require('minecraft-data')(this.bot.version));
            this.bot.pathfinder.setMovements(defaultMove);
            await this.bot.pathfinder.goto(new goals.GoalFollow(entity, 1));
            this.bot.attack(entity);
        } finally {
            this.state.currentAction = null;
        }
    }
}

module.exports = { BotManager };
